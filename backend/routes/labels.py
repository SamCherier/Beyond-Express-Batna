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
    Draw a single thermal label (10x15cm)
    Style: Yalidine-inspired with large COD amount and QR code
    """
    # Label dimensions (10x15cm = 100x150mm)
    label_width = 100 * mm_unit
    label_height = 150 * mm_unit
    
    # Start position
    x_start = 5 * mm_unit
    y_start = y_offset
    
    # === HEADER: Beyond Express Logo ===
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(label_width / 2, y_start + label_height - 15 * mm_unit, "BEYOND EXPRESS")
    
    # Horizontal line
    c.setStrokeColorRGB(0.8, 0.1, 0.1)  # Red
    c.setLineWidth(2)
    c.line(x_start, y_start + label_height - 20 * mm_unit, 
           label_width - x_start, y_start + label_height - 20 * mm_unit)
    
    # === CENTER: COD AMOUNT (VERY LARGE) ===
    cod_amount = order.get('cod_amount', 0)
    c.setFont("Helvetica-Bold", 40)
    c.drawCentredString(label_width / 2, y_start + label_height - 50 * mm_unit, 
                        f"{int(cod_amount)} DZD")
    
    c.setFont("Helvetica", 12)
    c.drawCentredString(label_width / 2, y_start + label_height - 60 * mm_unit, 
                        "Montant à Encaisser")
    
    # === MIDDLE: Recipient Info ===
    recipient = order.get('recipient', {})
    y_pos = y_start + label_height - 75 * mm_unit
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x_start, y_pos, f"Client: {recipient.get('name', 'N/A')}")
    y_pos -= 8 * mm_unit
    
    c.setFont("Helvetica", 12)
    c.drawString(x_start, y_pos, f"Tél: {recipient.get('phone', 'N/A')}")
    y_pos -= 8 * mm_unit
    
    c.drawString(x_start, y_pos, f"Adresse: {recipient.get('address', 'N/A')[:35]}...")
    y_pos -= 8 * mm_unit
    
    # === BOTTOM: Wilaya/Commune (LARGE) ===
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(label_width / 2, y_start + 60 * mm_unit, 
                        f"{recipient.get('wilaya', 'N/A')} - {recipient.get('commune', 'N/A')}")
    
    # === QR CODE ===
    tracking_id = order.get('tracking_id', 'N/A')
    qr_data = f"BEX-{tracking_id}"
    qr_buffer = generate_qr_code(qr_data)
    qr_img = ImageReader(qr_buffer)
    
    # Draw QR code (centered at bottom)
    qr_size = 35 * mm_unit
    qr_x = (label_width - qr_size) / 2
    qr_y = y_start + 15 * mm_unit
    c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)
    
    # Tracking ID below QR
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(label_width / 2, y_start + 10 * mm_unit, tracking_id)
    
    # Date
    created_at = order.get('created_at', '')
    if isinstance(created_at, str):
        date_str = created_at.split('T')[0]
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    c.setFont("Helvetica", 8)
    c.drawCentredString(label_width / 2, y_start + 5 * mm_unit, f"Date: {date_str}")
    
    # Border around label
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    c.rect(x_start / 2, y_start, label_width - x_start / 2, label_height)

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
        
        # Thermal label size: 10x15cm (100x150mm)
        label_width = 100 * mm_unit
        label_height = 150 * mm_unit
        
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
