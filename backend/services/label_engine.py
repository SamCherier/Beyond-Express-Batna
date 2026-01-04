"""
Unified Label Generator Engine
Generates A6 thermal labels (10x15cm) for all carriers

Features:
  - Multi-carrier support (Yalidine, ZR Express, etc.)
  - QR Code generation with tracking info
  - Barcode support
  - PDF merge for bulk printing
  - A6 format (100mm x 150mm) - Standard thermal printer format
"""
import io
import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import qrcode
from PIL import Image

from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128

from PyPDF2 import PdfMerger, PdfReader

logger = logging.getLogger(__name__)

# A6 size in points (100mm x 150mm)
A6_WIDTH = 100 * mm
A6_HEIGHT = 150 * mm


class LabelGenerator:
    """
    Unified Label Generator for all carriers
    
    Generates standardized A6 thermal labels with:
    - Carrier logo and branding
    - QR Code with tracking info
    - Barcode
    - Recipient info
    - COD amount (prominent)
    - Sender info
    """
    
    # Carrier colors for branding
    CARRIER_COLORS = {
        "yalidine": (220, 53, 69),      # Red
        "zr_express": (0, 123, 255),     # Blue
        "dhd": (40, 167, 69),            # Green
        "maystro": (255, 193, 7),        # Yellow/Gold
        "default": (108, 117, 125)       # Gray
    }
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for labels"""
        # Large tracking ID
        self.styles.add(ParagraphStyle(
            name='TrackingID',
            parent=self.styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=5,
            fontName='Helvetica-Bold'
        ))
        
        # Very large COD amount
        self.styles.add(ParagraphStyle(
            name='CODAmount',
            parent=self.styles['Heading1'],
            fontSize=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#DC3545'),
            spaceAfter=5,
            fontName='Helvetica-Bold'
        ))
        
        # Recipient name
        self.styles.add(ParagraphStyle(
            name='RecipientName',
            parent=self.styles['Normal'],
            fontSize=14,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Address style
        self.styles.add(ParagraphStyle(
            name='Address',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            fontName='Helvetica'
        ))
        
        # Wilaya (large)
        self.styles.add(ParagraphStyle(
            name='Wilaya',
            parent=self.styles['Heading2'],
            fontSize=16,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#0D6EFD')
        ))
        
        # Small text
        self.styles.add(ParagraphStyle(
            name='Small',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
    
    def _generate_qr_code(self, data: str, size: int = 80) -> io.BytesIO:
        """Generate QR code as image buffer"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
    
    def _draw_barcode(self, c: canvas.Canvas, tracking_id: str, x: float, y: float, width: float = 70*mm):
        """Draw barcode on canvas"""
        try:
            barcode = code128.Code128(tracking_id, barWidth=0.5*mm, barHeight=12*mm)
            barcode.drawOn(c, x, y)
        except Exception as e:
            logger.warning(f"Failed to draw barcode: {e}")
    
    def _get_carrier_color(self, carrier_type: str) -> Tuple[int, int, int]:
        """Get RGB color for carrier"""
        return self.CARRIER_COLORS.get(carrier_type, self.CARRIER_COLORS["default"])
    
    def generate_single_label(self, order: Dict[str, Any]) -> io.BytesIO:
        """
        Generate a single A6 label PDF for an order
        
        Args:
            order: Order data with recipient, tracking, COD info
            
        Returns:
            BytesIO buffer containing PDF
        """
        buffer = io.BytesIO()
        
        # Create canvas for A6 page
        c = canvas.Canvas(buffer, pagesize=(A6_WIDTH, A6_HEIGHT))
        
        recipient = order.get('recipient', {})
        carrier_type = order.get('carrier_type', 'default')
        carrier_tracking = order.get('carrier_tracking_id', order.get('tracking_id', 'N/A'))
        cod_amount = order.get('cod_amount', 0)
        
        # Get carrier color
        r, g, b = self._get_carrier_color(carrier_type)
        carrier_color = colors.Color(r/255, g/255, b/255)
        
        # === HEADER SECTION (Top) ===
        # Carrier banner
        c.setFillColor(carrier_color)
        c.rect(0, A6_HEIGHT - 20*mm, A6_WIDTH, 20*mm, fill=1, stroke=0)
        
        # Carrier name
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        carrier_name = carrier_type.replace('_', ' ').upper()
        c.drawCentredString(A6_WIDTH/2, A6_HEIGHT - 13*mm, carrier_name)
        
        # === QR CODE SECTION ===
        qr_data = f"{carrier_tracking}|{recipient.get('name','')}|{recipient.get('phone','')}"
        qr_buffer = self._generate_qr_code(qr_data, size=70)
        qr_img = RLImage(qr_buffer, width=25*mm, height=25*mm)
        qr_img.drawOn(c, 5*mm, A6_HEIGHT - 48*mm)
        
        # === TRACKING ID (Large) ===
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(35*mm, A6_HEIGHT - 30*mm, carrier_tracking)
        
        # Internal tracking (smaller)
        internal_tracking = order.get('tracking_id', '')
        if internal_tracking and internal_tracking != carrier_tracking:
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.gray)
            c.drawString(35*mm, A6_HEIGHT - 36*mm, f"Ref: {internal_tracking}")
        
        # Date
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.gray)
        c.drawString(35*mm, A6_HEIGHT - 42*mm, datetime.now().strftime("%d/%m/%Y %H:%M"))
        
        # === SEPARATOR LINE ===
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.5)
        c.line(5*mm, A6_HEIGHT - 52*mm, A6_WIDTH - 5*mm, A6_HEIGHT - 52*mm)
        
        # === RECIPIENT SECTION ===
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(5*mm, A6_HEIGHT - 60*mm, "DESTINATAIRE")
        
        c.setFont("Helvetica-Bold", 14)
        recipient_name = recipient.get('name', 'N/A')[:30]
        c.drawString(5*mm, A6_HEIGHT - 68*mm, recipient_name)
        
        c.setFont("Helvetica", 11)
        phone = recipient.get('phone', 'N/A')
        c.drawString(5*mm, A6_HEIGHT - 76*mm, f"📱 {phone}")
        
        # === WILAYA / COMMUNE (Prominent) ===
        c.setFillColor(carrier_color)
        c.setFont("Helvetica-Bold", 18)
        wilaya = recipient.get('wilaya', 'N/A')
        c.drawCentredString(A6_WIDTH/2, A6_HEIGHT - 90*mm, wilaya.upper())
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        commune = recipient.get('commune', '')
        c.drawCentredString(A6_WIDTH/2, A6_HEIGHT - 98*mm, commune)
        
        # Address
        c.setFont("Helvetica", 9)
        address = recipient.get('address', '')[:50]
        c.drawCentredString(A6_WIDTH/2, A6_HEIGHT - 106*mm, address)
        
        # === SEPARATOR LINE ===
        c.line(5*mm, A6_HEIGHT - 112*mm, A6_WIDTH - 5*mm, A6_HEIGHT - 112*mm)
        
        # === COD AMOUNT (VERY LARGE) ===
        c.setFillColor(colors.HexColor('#DC3545'))
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(A6_WIDTH/2, A6_HEIGHT - 120*mm, "MONTANT À ENCAISSER")
        
        c.setFont("Helvetica-Bold", 32)
        cod_text = f"{cod_amount:,.0f} DA".replace(',', ' ')
        c.drawCentredString(A6_WIDTH/2, A6_HEIGHT - 135*mm, cod_text)
        
        # === BARCODE (Bottom) ===
        try:
            self._draw_barcode(c, carrier_tracking, 15*mm, 8*mm)
        except:
            pass
        
        # === FOOTER ===
        c.setFillColor(colors.gray)
        c.setFont("Helvetica", 6)
        c.drawCentredString(A6_WIDTH/2, 3*mm, f"Beyond Express - {datetime.now().strftime('%Y')}")
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def generate_bulk_labels(self, orders: List[Dict[str, Any]]) -> io.BytesIO:
        """
        Generate multiple labels merged into a single PDF
        
        Args:
            orders: List of order data
            
        Returns:
            BytesIO buffer containing merged PDF
        """
        if not orders:
            raise ValueError("No orders provided")
        
        merger = PdfMerger()
        
        for order in orders:
            try:
                label_pdf = self.generate_single_label(order)
                merger.append(PdfReader(label_pdf))
                logger.info(f"✅ Label generated for {order.get('tracking_id', 'N/A')}")
            except Exception as e:
                logger.error(f"❌ Failed to generate label for {order.get('id', 'N/A')}: {e}")
                continue
        
        # Merge all PDFs
        output = io.BytesIO()
        merger.write(output)
        merger.close()
        output.seek(0)
        
        logger.info(f"📄 Generated bulk PDF with {len(orders)} labels")
        return output
    
    async def generate_carrier_label(
        self,
        order: Dict[str, Any],
        carrier_instance: Optional[Any] = None
    ) -> io.BytesIO:
        """
        Generate label with carrier-specific handling
        
        For Yalidine: Try to fetch official label, fallback to generated
        For others: Generate standard label
        """
        carrier_type = order.get('carrier_type', '')
        carrier_tracking = order.get('carrier_tracking_id', '')
        
        # Try to get official label from carrier API
        if carrier_instance and carrier_tracking:
            try:
                official_label = await carrier_instance.get_label(carrier_tracking)
                if official_label:
                    logger.info(f"✅ Using official {carrier_type} label for {carrier_tracking}")
                    return io.BytesIO(official_label)
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch official label: {e}")
        
        # Fallback to generated label
        logger.info(f"📝 Generating standard label for {carrier_tracking}")
        return self.generate_single_label(order)


# Singleton instance
_label_generator: Optional[LabelGenerator] = None

def get_label_generator() -> LabelGenerator:
    """Get or create label generator singleton"""
    global _label_generator
    if _label_generator is None:
        _label_generator = LabelGenerator()
    return _label_generator
