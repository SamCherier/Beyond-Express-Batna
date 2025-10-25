from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from io import BytesIO
import os
from datetime import datetime
import random

# Mapping des transporteurs vers leurs logos
TRANSPORTEUR_LOGOS = {
    'Yalidine': 'logo Yalidine.png',
    'DHD': 'logo DHD Livraison.png',
    'ZR EXPRESS': 'logo ZR eXPRESS.jpg',
    'Maystro': 'logo Maystro Delivery.png',
    'ECOTRACK': 'logo EcoTrack.png',
    'EcoTrack': 'logo EcoTrack.png',
    'NOEST': 'logo Noest.png',
    'Noest': 'logo Noest.png',
    'GUEPEX': 'logo Guepex.png',
    'Guepex': 'logo Guepex.png',
    'KAZI TOUR': 'logo Kazi Tour.png',
    'Kazi Tour': 'logo Kazi Tour.png',
    'Lynx Express': 'logo Lynx Express.png',
    'DHL': 'logo DHL.png',
    'EMS': 'logo EMS.png',
    'ARAMEX': 'logo ARAMEX.png',
    'Aramex': 'logo ARAMEX.png',
    'ANDERSON': 'logo ANDERSON.png',
}

WILAYA_CODES = {
    "Adrar": "01", "Chlef": "02", "Laghouat": "03", "Oum El Bouaghi": "04", "Batna": "05",
    "Béjaïa": "06", "Biskra": "07", "Béchar": "08", "Blida": "09", "Bouira": "10",
    "Tamanrasset": "11", "Tébessa": "12", "Tlemcen": "13", "Tiaret": "14", "Tizi Ouzou": "15",
    "Alger": "16", "Djelfa": "17", "Jijel": "18", "Sétif": "19", "Saïda": "20",
    "Skikda": "21", "Sidi Bel Abbès": "22", "Annaba": "23", "Guelma": "24", "Constantine": "25",
    "Médéa": "26", "Mostaganem": "27", "M'Sila": "28", "Mascara": "29", "Ouargla": "30",
    "Oran": "31", "El Bayadh": "32", "Illizi": "33", "Bordj Bou Arréridj": "34", "Boumerdès": "35",
    "El Tarf": "36", "Tindouf": "37", "Tissemsilt": "38", "El Oued": "39", "Khenchela": "40",
    "Souk Ahras": "41", "Tipaza": "42", "Mila": "43", "Aïn Defla": "44", "Naâma": "45",
    "Aïn Témouchent": "46", "Ghardaïa": "47", "Relizane": "48"
}

def generate_qr_code(data: str) -> BytesIO:
    """Generate QR code for tracking"""
    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def generate_pin_code() -> str:
    """Generate random 4-digit PIN code"""
    return str(random.randint(1000, 9999))

def get_logo_path(logo_type: str, delivery_partner: str = None) -> str:
    """Get the logo path"""
    if logo_type == 'beyond':
        logo_path = os.path.join(
            os.path.dirname(__file__), 
            'static', 
            'logos', 
            'beyond_express_logo_1.jpg'
        )
        return logo_path if os.path.exists(logo_path) else None
    
    elif logo_type == 'transporteur' and delivery_partner:
        logo_filename = TRANSPORTEUR_LOGOS.get(delivery_partner)
        if not logo_filename:
            return None
        
        logo_path = os.path.join(
            os.path.dirname(__file__), 
            'static', 
            'logos', 
            'transporteurs',
            logo_filename
        )
        return logo_path if os.path.exists(logo_path) else None
    
    return None

def create_single_bordereau(c: canvas.Canvas, order_data: dict, x_offset: float, y_offset: float):
    """
    Create a single bordereau at specified position
    Each bordereau is 105mm x 148.5mm (quarter of A4)
    """
    # Dimensions
    bordereau_width = 105*mm
    bordereau_height = 148.5*mm
    
    # Get data
    tracking_id = order_data.get('tracking_id', 'N/A')
    delivery_partner = order_data.get('delivery_partner', 'N/A')
    wilaya_code = WILAYA_CODES.get(order_data['recipient']['wilaya'], '00')
    wilaya_name = order_data['recipient']['wilaya']
    commune_name = order_data['recipient']['commune']
    cod_amount = order_data.get('cod_amount', 0)
    description = order_data.get('description', 'N/A')
    pin_code = generate_pin_code()
    sender_name = order_data['sender']['name']
    recipient_name = order_data['recipient']['name']
    recipient_phone = order_data['recipient']['phone']
    sender_wilaya = order_data['sender']['wilaya']
    
    # ===== DRAW BORDER =====
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    c.rect(x_offset, y_offset, bordereau_width, bordereau_height)
    
    # Current Y position (start from top)
    current_y = y_offset + bordereau_height - 5*mm
    
    # ===== 1. HEADER WITH LOGOS =====
    beyond_logo_path = get_logo_path('beyond')
    transporteur_logo_path = get_logo_path('transporteur', delivery_partner)
    
    if beyond_logo_path and os.path.exists(beyond_logo_path):
        try:
            c.drawImage(beyond_logo_path, x_offset + 5*mm, current_y - 15*mm, 
                       width=20*mm, height=20*mm, preserveAspectRatio=True, mask='auto')
        except:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_offset + 5*mm, current_y - 10*mm, "BEYOND EXPRESS")
    else:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_offset + 5*mm, current_y - 10*mm, "BEYOND EXPRESS")
    
    if transporteur_logo_path and os.path.exists(transporteur_logo_path):
        try:
            c.drawImage(transporteur_logo_path, x_offset + bordereau_width - 25*mm, current_y - 15*mm,
                       width=20*mm, height=20*mm, preserveAspectRatio=True, mask='auto')
        except:
            pass
    
    current_y -= 20*mm
    
    # Service type badge
    c.setFillColor(colors.HexColor('#FF5757'))
    c.rect(x_offset + 30*mm, current_y - 5*mm, 25*mm, 5*mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x_offset + 42.5*mm, current_y - 4*mm, "E-COMMERCE")
    c.setFillColor(colors.black)
    
    current_y -= 10*mm
    
    # ===== 2. SENDER SECTION =====
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x_offset + 5*mm, current_y, "Expéditeur")
    current_y -= 4*mm
    c.setFont("Helvetica", 7)
    c.drawString(x_offset + 5*mm, current_y, sender_name)
    current_y -= 3*mm
    c.drawString(x_offset + 5*mm, current_y, f"{order_data['sender']['commune']}, {order_data['sender']['wilaya']}")
    current_y -= 3*mm
    c.drawString(x_offset + 5*mm, current_y, order_data['sender']['phone'])
    
    current_y -= 8*mm
    
    # ===== 3. RECIPIENT + HUGE WILAYA NUMBER =====
    # Recipient section (left side)
    recipient_y = current_y
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x_offset + 5*mm, recipient_y, "Destinataire")
    recipient_y -= 4*mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_offset + 5*mm, recipient_y, recipient_name[0].upper())
    recipient_y -= 4*mm
    c.setFont("Helvetica", 7)
    c.drawString(x_offset + 5*mm, recipient_y, f"Agence de {commune_name}")
    recipient_y -= 3*mm
    c.drawString(x_offset + 5*mm, recipient_y, f"{wilaya_name}, {wilaya_name}")
    recipient_y -= 3*mm
    c.drawString(x_offset + 5*mm, recipient_y, recipient_phone)
    
    # HUGE Wilaya number (right side)
    c.setFont("Helvetica-Bold", 48)
    c.drawCentredString(x_offset + bordereau_width - 20*mm, current_y - 15*mm, wilaya_code)
    
    current_y -= 30*mm
    
    # ===== 4. QR CODE + TRACKING + PIN =====
    # QR Code
    qr_buffer = generate_qr_code(tracking_id)
    qr_buffer.seek(0)  # Reset buffer position
    try:
        from PIL import Image as PILImage
        # Save to temp file for reliable rendering
        qr_temp_path = f'/tmp/qr_{tracking_id}.png'
        with open(qr_temp_path, 'wb') as f:
            f.write(qr_buffer.read())
        c.drawImage(qr_temp_path, x_offset + 5*mm, current_y - 20*mm, 
                   width=20*mm, height=20*mm, preserveAspectRatio=True)
        # Clean up
        try:
            os.remove(qr_temp_path)
        except:
            pass
    except Exception as e:
        # Fallback: draw a box where QR should be
        c.setStrokeColor(colors.black)
        c.rect(x_offset + 5*mm, current_y - 20*mm, 20*mm, 20*mm)
        c.setFont("Helvetica", 6)
        c.drawString(x_offset + 7*mm, current_y - 11*mm, "QR CODE")
    
    # Tracking ID and PIN
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_offset + 30*mm, current_y - 8*mm, tracking_id)
    c.setFont("Helvetica", 8)
    c.drawString(x_offset + 30*mm, current_y - 13*mm, f"PIN: {pin_code}")
    
    current_y -= 25*mm
    
    # ===== 5. CONTENT TABLE =====
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x_offset + 5*mm, current_y, "Description du contenu")
    c.drawString(x_offset + 60*mm, current_y, "Valeur (DZD)")
    
    current_y -= 1*mm
    c.setStrokeColor(colors.grey)
    c.line(x_offset + 5*mm, current_y, x_offset + bordereau_width - 5*mm, current_y)
    
    current_y -= 4*mm
    c.setFont("Helvetica", 7)
    c.drawString(x_offset + 5*mm, current_y, description[:30])
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x_offset + 60*mm, current_y, f"{cod_amount} DA")
    
    current_y -= 8*mm
    
    # ===== 6. FOOTER =====
    c.setFont("Helvetica", 6)
    c.drawString(x_offset + 5*mm, current_y, f"Départ: {sender_wilaya}")
    current_y -= 3*mm
    c.drawString(x_offset + 5*mm, current_y, f"le: {datetime.now().strftime('%d/%m/%Y')}")
    current_y -= 3*mm
    c.drawString(x_offset + 5*mm, current_y, "Signature: _______________")
    
    current_y -= 5*mm
    
    # Legal text
    legal_text = f"{sender_name} certifie que les details declares sur ce bordereau sont corrects et que le colis ne contient aucun produit dangereux, interdit par la loi ou par les conditions generales de transport {delivery_partner}."
    c.setFont("Helvetica", 5)
    
    # Wrap text to fit width
    max_width = bordereau_width - 10*mm
    words = legal_text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if c.stringWidth(test_line, "Helvetica", 5) < max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    
    for line in lines[:3]:  # Max 3 lines
        c.drawString(x_offset + 5*mm, current_y, line)
        current_y -= 2.5*mm

def generate_bordereau_pdf_yalidine_format(order_data: dict) -> BytesIO:
    """
    Generate PDF with 2 copies of bordereau per page (2x1 layout on A4)
    Format: 2 bordereaux side by side
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    width, height = A4
    
    # Draw 2 bordereaux side by side (left and right)
    # Left bordereau
    create_single_bordereau(c, order_data, 0, height - 148.5*mm)
    
    # Right bordereau (same order data for duplicate)
    create_single_bordereau(c, order_data, 105*mm, height - 148.5*mm)
    
    # Add cut line in the middle
    c.setStrokeColor(colors.lightgrey)
    c.setDash(3, 3)
    c.line(105*mm, 0, 105*mm, height)
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer

# Alias for backward compatibility
generate_bordereau_pdf = generate_bordereau_pdf_yalidine_format
generate_bordereau_pdf_final = generate_bordereau_pdf_yalidine_format
generate_bordereau_pdf_modern = generate_bordereau_pdf_yalidine_format
