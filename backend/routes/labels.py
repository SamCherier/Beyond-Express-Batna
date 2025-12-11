"""
Shipping Labels Generation Routes
Generates thermal sticker labels (10x15cm) for orders
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from typing import List
import os
import logging
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm as mm_unit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import qrcode

from models import User
from auth_utils import verify_token

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Auth dependency
from fastapi import Request, Cookie
from typing import Optional

async def get_current_user(request: Request, session_token: Optional[str] = Cookie(None)) -> User:
    """Auth dependency"""
    token = session_token
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.sessions.find_one({"session_token": token}, {"_id": 0})
    if session_doc:
        if datetime.fromisoformat(session_doc['expires_at']) > datetime.now(timezone.utc):
            user_doc = await db.users.find_one({"id": session_doc['user_id']}, {"_id": 0})
            if user_doc:
                return User(**user_doc)
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)

def generate_qr_code(data: str) -> BytesIO:
    """Generate QR code image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer

def draw_label(c, order: dict, y_offset: float = 0):
    """
    Draw a single thermal label A6 (105mm x 148mm)
    Professional Yalidine-inspired design with proper spacing and word wrap
    """
    # A6 dimensions (105mm x 148mm) with 5mm safety margins
    label_width = 105 * mm_unit
    label_height = 148 * mm_unit
    margin = 5 * mm_unit
    
    # Working area
    x_start = margin
    x_end = label_width - margin
    y_start = margin
    y_end = label_height - margin
    working_width = x_end - x_start
    
    # Current Y position (top to bottom)
    y_pos = y_end
    
    # === HEADER: Logo (Left) | Date (Right) ===
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x_start, y_pos, "BEYOND EXPRESS")
    
    created_at = order.get('created_at', '')
    if isinstance(created_at, str):
        date_str = created_at.split('T')[0]
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    c.setFont("Helvetica", 8)
    c.drawRightString(x_end, y_pos, f"Date: {date_str}")
    y_pos -= 6 * mm_unit
    
    # Red line separator
    c.setStrokeColorRGB(0.8, 0.1, 0.1)
    c.setLineWidth(1.5)
    c.line(x_start, y_pos, x_end, y_pos)
    y_pos -= 5 * mm_unit
    
    # === ZONE EXPÉDITEUR (Small Box) ===
    sender_box_height = 12 * mm_unit
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)
    c.rect(x_start, y_pos - sender_box_height, working_width, sender_box_height)
    
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x_start + 2 * mm_unit, y_pos - 4 * mm_unit, "EXPÉDITEUR")
    c.setFont("Helvetica", 7)
    c.drawString(x_start + 2 * mm_unit, y_pos - 8 * mm_unit, "BEYOND EXPRESS - Batna")
    c.drawString(x_start + 2 * mm_unit, y_pos - 11 * mm_unit, "Tél: 0550000000")
    
    y_pos -= sender_box_height + 4 * mm_unit
    
    # === ZONE DESTINATAIRE (Large Box) ===
    recipient = order.get('recipient', {})
    dest_box_height = 35 * mm_unit
    c.setLineWidth(1)
    c.rect(x_start, y_pos - dest_box_height, working_width, dest_box_height)
    
    # Recipient header
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_start + 2 * mm_unit, y_pos - 5 * mm_unit, "DESTINATAIRE")
    
    # Name
    c.setFont("Helvetica-Bold", 10)
    recipient_name = recipient.get('name', 'N/A')
    c.drawString(x_start + 2 * mm_unit, y_pos - 10 * mm_unit, recipient_name[:30])
    
    # Phone
    c.setFont("Helvetica", 9)
    c.drawString(x_start + 2 * mm_unit, y_pos - 14 * mm_unit, f"Tél: {recipient.get('phone', 'N/A')}")
    
    # Wilaya/Commune
    c.setFont("Helvetica-Bold", 10)
    wilaya_commune = f"{recipient.get('wilaya', 'N/A')} - {recipient.get('commune', 'N/A')}"
    c.drawString(x_start + 2 * mm_unit, y_pos - 19 * mm_unit, wilaya_commune[:35])
    
    # Address with word wrap
    c.setFont("Helvetica", 8)
    address = recipient.get('address', 'N/A')
    max_chars_per_line = 45
    
    # Split address into lines
    words = address.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line + " " + word) <= max_chars_per_line:
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Draw address lines (max 3 lines)
    address_y = y_pos - 24 * mm_unit
    for i, line in enumerate(lines[:3]):
        c.drawString(x_start + 2 * mm_unit, address_y - (i * 3.5 * mm_unit), line)
    
    y_pos -= dest_box_height + 4 * mm_unit
    
    # === ZONE COD (HUGE and BOLD) ===
    cod_amount = order.get('cod_amount', 0)
    cod_box_height = 20 * mm_unit
    
    # COD Box with thick border
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(2)
    c.rect(x_start, y_pos - cod_box_height, working_width, cod_box_height)
    
    # COD Label
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x_start + working_width / 2, y_pos - 5 * mm_unit, "MONTANT À ENCAISSER")
    
    # COD Amount (HUGE)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(x_start + working_width / 2, y_pos - 16 * mm_unit, f"{int(cod_amount)} DA")
    
    y_pos -= cod_box_height + 4 * mm_unit
    
    # === FOOTER: QR Code + Tracking ID ===
    tracking_id = order.get('tracking_id', 'N/A')
    qr_data = f"BEX-{tracking_id}"
    qr_buffer = generate_qr_code(qr_data)
    qr_img = ImageReader(qr_buffer)
    
    # QR Code (centered)
    qr_size = 25 * mm_unit
    qr_x = x_start + (working_width - qr_size) / 2
    c.drawImage(qr_img, qr_x, y_pos - qr_size, width=qr_size, height=qr_size)
    
    # Tracking ID below QR
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x_start + working_width / 2, y_pos - qr_size - 4 * mm_unit, tracking_id)
    
    # Outer border for entire label
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(2)
    c.rect(0, 0, label_width, label_height)

@router.post("/print-labels")
async def print_shipping_labels(
    order_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """
    Generate thermal shipping labels (10x15cm) for multiple orders
    One page per order
    """
    try:
        if not order_ids:
            raise HTTPException(status_code=400, detail="No order IDs provided")
        
        # Fetch orders
        orders = await db.orders.find(
            {"id": {"$in": order_ids}},
            {"_id": 0}
        ).to_list(1000)
        
        if not orders:
            raise HTTPException(status_code=404, detail="No orders found")
        
        # Create PDF
        buffer = BytesIO()
        
        # A6 label size: 105mm x 148mm (standard thermal size)
        label_width = 105 * mm_unit
        label_height = 148 * mm_unit
        
        c = canvas.Canvas(buffer, pagesize=(label_width, label_height))
        
        # Generate one label per page
        for order in orders:
            draw_label(c, order, y_offset=0)
            c.showPage()  # New page for next label
        
        c.save()
        buffer.seek(0)
        
        logger.info(f"✅ Generated {len(orders)} shipping labels")
        
        # Return as downloadable PDF
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                'Content-Disposition': f'attachment; filename="etiquettes_commandes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating labels: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
