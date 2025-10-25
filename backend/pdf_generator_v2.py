from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import qrcode
from io import BytesIO
import os
from datetime import datetime

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
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def get_transporteur_logo_path(delivery_partner: str) -> str:
    """Get the logo path for a delivery partner"""
    if not delivery_partner:
        return None
    
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
    
    if os.path.exists(logo_path):
        return logo_path
    return None

def generate_bordereau_pdf_modern(order_data: dict) -> BytesIO:
    """
    Generate a modern, single-page bordereau PDF with dynamic logos
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=15*mm, 
        leftMargin=15*mm,
        topMargin=15*mm, 
        bottomMargin=15*mm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # ===== CUSTOM STYLES =====
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=16,
        textColor=colors.HexColor('#FF5757'),
        alignment=TA_CENTER,
        spaceAfter=2*mm,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=3*mm,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=2*mm
    )
    
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.grey
    )
    
    # ===== HEADER WITH DUAL LOGOS =====
    beyond_logo_path = os.path.join(
        os.path.dirname(__file__), 
        'static', 
        'logos', 
        'beyond_express_logo_1.jpg'
    )
    
    delivery_partner = order_data.get('delivery_partner')
    transporteur_logo_path = get_transporteur_logo_path(delivery_partner)
    
    # Create header table with logos
    header_data = []
    
    if os.path.exists(beyond_logo_path) and transporteur_logo_path:
        # Both logos available
        beyond_img = Image(beyond_logo_path, width=30*mm, height=30*mm)
        transporteur_img = Image(transporteur_logo_path, width=30*mm, height=30*mm)
        header_data = [[beyond_img, transporteur_img]]
        header_table = Table(header_data, colWidths=[9*cm, 9*cm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(header_table)
    elif os.path.exists(beyond_logo_path):
        # Only Beyond Express logo
        beyond_img = Image(beyond_logo_path, width=35*mm, height=35*mm)
        beyond_img.hAlign = 'CENTER'
        story.append(beyond_img)
    else:
        # Fallback to text
        story.append(Paragraph("<b>BEYOND EXPRESS</b>", title_style))
    
    story.append(Spacer(1, 5*mm))
    
    # ===== MAIN CONTENT - COMPACT LAYOUT =====
    tracking_id = order_data.get('tracking_id', '')
    wilaya_code = WILAYA_CODES.get(order_data['recipient']['wilaya'], '00')
    
    # Generate QR Code (smaller for single page)
    qr_buffer = generate_qr_code(tracking_id)
    qr_img = Image(qr_buffer, width=45*mm, height=45*mm)
    
    # ===== LEFT SIDE: SENDER & RECIPIENT | RIGHT SIDE: QR + TRACKING =====
    
    # Create a simpler, cleaner layout using nested tables
    # Sender info box
    sender_table = Table([
        [Paragraph("<b>EXPÉDITEUR</b>", header_style)],
        [Paragraph(f"<b>{order_data['sender']['name']}</b>", normal_style)],
        [Paragraph(f"{order_data['sender']['address']}", small_style)],
        [Paragraph(f"{order_data['sender']['commune']}, {order_data['sender']['wilaya']}", small_style)],
        [Paragraph(f"Tél: {order_data['sender']['phone']}", small_style)],
    ], colWidths=[10*cm])
    sender_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#FF5757')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#FFF8F8')),
        ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
    ]))
    
    # QR and tracking box
    qr_tracking_table = Table([
        [Paragraph("<b>N° SUIVI</b>", header_style)],
        [Paragraph(f"<font size=14><b>{tracking_id}</b></font>", ParagraphStyle(
            'TrackingNum',
            parent=normal_style,
            fontSize=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#FF5757')
        ))],
        [qr_img],
        [Paragraph(f"Wilaya: <b>{wilaya_code}</b>", small_style)],
    ], colWidths=[7.5*cm])
    qr_tracking_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F5F5F5')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
    ]))
    
    # Top row with sender and QR
    top_row_table = Table([[sender_table, qr_tracking_table]], colWidths=[10*cm, 7.5*cm])
    top_row_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(top_row_table)
    story.append(Spacer(1, 3*mm))
    
    # Recipient info box
    recipient_table = Table([
        [Paragraph("<b>DESTINATAIRE</b>", header_style)],
        [Paragraph(f"<b>{order_data['recipient']['name']}</b>", normal_style)],
        [Paragraph(f"Tél: <b>{order_data['recipient']['phone']}</b>", normal_style)],
        [Paragraph(f"{order_data['recipient']['address']}", small_style)],
        [Paragraph(f"<b>{order_data['recipient']['commune']}, {order_data['recipient']['wilaya']}</b>", small_style)],
    ], colWidths=[17.5*cm])
    recipient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#FF5757')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#FFF8F8')),
        ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
    ]))
    story.append(recipient_table)
    story.append(Spacer(1, 4*mm))
    
    # ===== PACKAGE DETAILS - COMPACT TABLE =====
    cod_amount = order_data.get('cod_amount', 0)
    description = order_data.get('description', 'N/A')
    service_type = order_data.get('service_type', 'Standard')
    delivery_partner_display = delivery_partner if delivery_partner else "Non spécifié"
    
    details_data = [
        ["Transporteur", delivery_partner_display, "Montant COD", f"{cod_amount} DA"],
        ["Description", description, "Service", service_type],
    ]
    
    details_table = Table(details_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FFE5E5')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#FFE5E5')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
        ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))
    
    story.append(details_table)
    story.append(Spacer(1, 5*mm))
    
    # ===== FOOTER - DECLARATION =====
    legal_text = f"""<i>Je certifie que les détails fournis sont exacts et que ce colis ne contient aucun produit dangereux. 
    Date: {datetime.now().strftime('%d/%m/%Y')} | Signature: ________________</i>"""
    
    story.append(Paragraph(legal_text, ParagraphStyle(
        'Legal',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.grey,
        alignment=TA_CENTER
    )))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
