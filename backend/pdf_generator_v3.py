from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
import qrcode
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
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def generate_barcode(data: str) -> Drawing:
    """Generate Code 128 barcode"""
    barcode = code128.Code128(data, barHeight=15*mm, barWidth=1.2)
    drawing = Drawing(barcode.width, barcode.height)
    drawing.add(barcode)
    return drawing

def generate_pin_code() -> str:
    """Generate random 4-digit PIN code"""
    return str(random.randint(1000, 9999))

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

def generate_bordereau_pdf_final(order_data: dict) -> BytesIO:
    """
    Generate final bordereau PDF with Yalidine-inspired modern design
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=10*mm, 
        leftMargin=10*mm,
        topMargin=10*mm, 
        bottomMargin=10*mm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # ===== CUSTOM STYLES =====
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=10,
        textColor=colors.black,
        spaceAfter=2*mm,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=1*mm
    )
    
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.black
    )
    
    wilaya_big_style = ParagraphStyle(
        'WilayaBig',
        parent=styles['Title'],
        fontSize=72,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=72
    )
    
    # ===== 1. HEADER WITH DUAL LOGOS =====
    beyond_logo_path = os.path.join(
        os.path.dirname(__file__), 
        'static', 
        'logos', 
        'beyond_express_logo_1.jpg'
    )
    
    delivery_partner = order_data.get('delivery_partner')
    transporteur_logo_path = get_transporteur_logo_path(delivery_partner)
    
    # Create header with logos
    if os.path.exists(beyond_logo_path) and transporteur_logo_path:
        beyond_img = Image(beyond_logo_path, width=25*mm, height=25*mm)
        transporteur_img = Image(transporteur_logo_path, width=25*mm, height=25*mm)
        
        header_table = Table([[beyond_img, '', transporteur_img]], colWidths=[6*cm, 7*cm, 6*cm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 3*mm))
    
    # Service type badge (E-COMMERCE or other)
    service_type = order_data.get('service_type', 'E-COMMERCE')
    service_badge = Table([[Paragraph(f"<b>{service_type}</b>", ParagraphStyle(
        'ServiceBadge',
        parent=normal_style,
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER
    ))]], colWidths=[4*cm])
    service_badge.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FF5757')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))
    story.append(service_badge)
    story.append(Spacer(1, 2*mm))
    
    # ===== 2. SENDER INFORMATION =====
    sender_data = [
        [Paragraph("<b>Expéditeur</b>", header_style)],
        [Paragraph(f"{order_data['sender']['name']}", normal_style)],
        [Paragraph(f"{order_data['sender']['commune']}, {order_data['sender']['wilaya']}", normal_style)],
        [Paragraph(f"{order_data['sender']['phone']}", normal_style)],
    ]
    
    sender_table = Table(sender_data, colWidths=[19*cm])
    sender_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F5F5F5')),
        ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(sender_table)
    story.append(Spacer(1, 3*mm))
    
    # ===== 3. MAIN CONTENT: RECIPIENT + WILAYA NUMBER =====
    tracking_id = order_data.get('tracking_id', '')
    wilaya_code = WILAYA_CODES.get(order_data['recipient']['wilaya'], '00')
    wilaya_name = order_data['recipient']['wilaya']
    commune_name = order_data['recipient']['commune']
    
    # Recipient info
    recipient_initial = order_data['recipient']['name'][0].upper()
    recipient_data = [
        [Paragraph("<b>Destinataire</b>", header_style)],
        [Paragraph(f"<b>{recipient_initial}</b>", ParagraphStyle(
            'RecipientInitial',
            parent=normal_style,
            fontSize=16,
            fontName='Helvetica-Bold'
        ))],
        [Paragraph(f"Agence de {commune_name}", normal_style)],
        [Paragraph(f"{wilaya_name}, {wilaya_name}", normal_style)],
        [Paragraph(f"{order_data['recipient']['phone']}", normal_style)],
    ]
    
    recipient_table = Table(recipient_data, colWidths=[10*cm])
    recipient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    # HUGE Wilaya number
    wilaya_display = [
        [Paragraph(f"<b>{wilaya_code}</b>", wilaya_big_style)],
    ]
    
    wilaya_table = Table(wilaya_display, colWidths=[9*cm])
    wilaya_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    # Combine recipient and wilaya
    main_row = Table([[recipient_table, wilaya_table]], colWidths=[10*cm, 9*cm])
    main_row.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(main_row)
    story.append(Spacer(1, 2*mm))
    
    # ===== 4. BARCODE + TRACKING CODE + PIN =====
    # Generate barcode
    barcode_drawing = generate_barcode(tracking_id)
    
    # PIN code
    pin_code = generate_pin_code()
    
    barcode_section = [
        [barcode_drawing],
        [Paragraph(f"<b>{tracking_id}</b>", ParagraphStyle(
            'TrackingCode',
            parent=normal_style,
            fontSize=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))],
        [Paragraph(f"PIN: <b>{pin_code}</b>", ParagraphStyle(
            'PinCode',
            parent=normal_style,
            fontSize=9,
            alignment=TA_CENTER
        ))],
    ]
    
    barcode_table = Table(barcode_section, colWidths=[19*cm])
    barcode_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))
    story.append(barcode_table)
    story.append(Spacer(1, 3*mm))
    
    # ===== 5. TYPE DE SERVICE =====
    delivery_type = order_data.get('delivery_type', 'Livraison à Domicile')
    
    type_service_table = Table([[Paragraph(f"<b>Type:</b> {delivery_type}", normal_style)]], colWidths=[19*cm])
    type_service_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFACD')),
        ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(type_service_table)
    story.append(Spacer(1, 3*mm))
    
    # ===== 6. CONTENT TABLE (Description + Value) =====
    cod_amount = order_data.get('cod_amount', 0)
    description = order_data.get('description', 'N/A')
    
    content_data = [
        [Paragraph("<b>Description du contenu</b>", normal_style), 
         Paragraph("<b>Valeur (DZD)</b>", normal_style)],
        [Paragraph(description, small_style), 
         Paragraph(f"<b>{cod_amount} DA</b>", normal_style)],
    ]
    
    content_table = Table(content_data, colWidths=[13*cm, 6*cm])
    content_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
    ]))
    story.append(content_table)
    story.append(Spacer(1, 3*mm))
    
    # ===== 7. FOOTER: DEPART, DATE, SIGNATURE, LEGAL TEXT =====
    depart_wilaya = order_data['sender']['wilaya']
    current_date = datetime.now().strftime('%d/%m/%Y')
    sender_name = order_data['sender']['name']
    transporteur_name = delivery_partner if delivery_partner else "le transporteur"
    
    footer_info = [
        [Paragraph(f"<b>Départ:</b> {depart_wilaya}", small_style)],
        [Paragraph(f"<b>le:</b> {current_date}", small_style)],
        [Paragraph("<b>Signature:</b> _________________", small_style)],
    ]
    
    footer_table = Table(footer_info, colWidths=[19*cm])
    footer_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
    ]))
    story.append(footer_table)
    story.append(Spacer(1, 2*mm))
    
    # Legal text
    legal_text = f"""<i>{sender_name} certifie que les détails déclarés sur ce bordereau sont corrects et que le colis ne contient aucun produit dangereux, interdit par la loi ou par les conditions générales de transport {transporteur_name}.</i>"""
    
    story.append(Paragraph(legal_text, ParagraphStyle(
        'Legal',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.grey,
        alignment=TA_LEFT,
        leftIndent=3*mm
    )))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# Alias for backward compatibility
generate_bordereau_pdf_modern = generate_bordereau_pdf_final
