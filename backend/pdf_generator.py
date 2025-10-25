from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import qrcode
from io import BytesIO
import os
from datetime import datetime
from PIL import Image as PILImage

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

def generate_bordereau_pdf(order_data: dict) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=10*mm, leftMargin=10*mm,
                            topMargin=10*mm, bottomMargin=10*mm)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#FF5757'),
        alignment=TA_CENTER,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Title'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#FF5757'),
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    # ===== HEADER WITH LOGO AND BRANDING =====
    # Try to load the Beyond Express logo
    logo_path = os.path.join(os.path.dirname(__file__), 'static', 'logos', 'beyond_express_logo_1.jpg')
    
    if os.path.exists(logo_path):
        try:
            # Load and resize logo
            logo_img = Image(logo_path, width=40*mm, height=40*mm)
            logo_img.hAlign = 'CENTER'
            story.append(logo_img)
            story.append(Spacer(1, 3*mm))
        except Exception as e:
            print(f"Error loading logo: {e}")
            # Fallback to text-only header
            story.append(Paragraph("<b>BEYOND EXPRESS</b>", title_style))
    else:
        # Fallback if logo doesn't exist
        story.append(Paragraph("<b>BEYOND EXPRESS</b>", title_style))
    
    # Company Name
    story.append(Paragraph("<b>Beyond Express</b>", title_style))
    
    # Dynamic "BY [TRANSPORTEUR]" based on delivery partner
    delivery_partner = order_data.get('delivery_partner', 'TRANSPORTEUR')
    story.append(Paragraph(f"<b>BY {delivery_partner.upper()}</b>", subtitle_style))
    story.append(Spacer(1, 5*mm))
    
    # Generate QR Code
    tracking_id = order_data.get('tracking_id', '')
    qr_buffer = generate_qr_code(tracking_id)
    qr_img = Image(qr_buffer, width=60*mm, height=60*mm)
    
    # Main table with order info
    wilaya_code = WILAYA_CODES.get(order_data['recipient']['wilaya'], '00')
    
    # Sender info
    story.append(Paragraph("<b>EXPÉDITEUR / SENDER</b>", header_style))
    sender_data = [
        ["Beyond Express"],
        [order_data['sender']['address']],
        [f"{order_data['sender']['wilaya']}, {order_data['sender']['commune']}"],
        [f"Tél: {order_data['sender']['phone']}"],
        ["Email: contact@beyondexpress.com"]
    ]
    sender_table = Table(sender_data, colWidths=[18*cm])
    sender_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF5F5')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(sender_table)
    story.append(Spacer(1, 5*mm))
    
    # Recipient info with QR code
    story.append(Paragraph("<b>DESTINATAIRE / RECIPIENT</b>", header_style))
    recipient_data = [
        [qr_img, [
            Paragraph(f"<b>{order_data['recipient']['name']}</b>", normal_style),
            Paragraph(f"Tél: <b>{order_data['recipient']['phone']}</b>", normal_style),
            Paragraph(f"{order_data['recipient']['address']}", normal_style),
            Paragraph(f"<b>{order_data['recipient']['commune']}, {order_data['recipient']['wilaya']}</b>", normal_style),
        ]]
    ]
    recipient_table = Table(recipient_data, colWidths=[6*cm, 12*cm])
    recipient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF5F5')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(recipient_table)
    story.append(Spacer(1, 5*mm))
    
    # Tracking and payment info
    story.append(Paragraph("<b>DÉTAILS DU COLIS / PACKAGE DETAILS</b>", header_style))
    details_data = [
        ["N° de suivi / Tracking:", f"<b>{tracking_id}</b>"],
        ["Code Wilaya:", f"<b>{wilaya_code}</b>"],
        ["Partenaire Livraison:", f"<b>{delivery_partner}</b>"],
        ["Montant COD:", f"<b>{order_data['cod_amount']} DA</b>"],
        ["Description:", order_data['description']],
        ["Type de service:", order_data['service_type']],
    ]
    details_table = Table(details_data, colWidths=[5*cm, 13*cm])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FFE5E5')),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(details_table)
    story.append(Spacer(1, 8*mm))
    
    # Legal declaration
    legal_text = f"""<i>Je, {order_data['sender']['name']}, certifie que les détails fournis sont exacts et que ce colis ne contient aucun produit dangereux ou interdit par la loi. Date: {datetime.now().strftime('%d/%m/%Y')}</i>"""
    story.append(Paragraph(legal_text, ParagraphStyle(
        'Legal',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )))
    
    doc.build(story)
    buffer.seek(0)
    return buffer