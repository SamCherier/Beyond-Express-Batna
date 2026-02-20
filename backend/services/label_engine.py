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
        Generate a single A6 label PDF for an order.
        Layout uses strict vertical zones to prevent overlap.
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(A6_WIDTH, A6_HEIGHT))

        recipient = order.get('recipient', {})
        carrier_type = order.get('carrier_type', 'default')
        carrier_tracking = order.get('carrier_tracking_id', order.get('tracking_id', 'N/A'))
        internal_tracking = order.get('tracking_id', '')
        cod_amount = order.get('cod_amount', 0)

        r, g, b = self._get_carrier_color(carrier_type)
        carrier_color = colors.Color(r/255, g/255, b/255)

        margin = 4 * mm

        # ── ZONE 1: Header banner (150mm → 135mm) ──
        banner_h = 15 * mm
        banner_y = A6_HEIGHT - banner_h
        c.setFillColor(carrier_color)
        c.rect(0, banner_y, A6_WIDTH, banner_h, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(A6_WIDTH / 2, banner_y + 4 * mm, carrier_type.replace('_', ' ').upper())

        # ── ZONE 2: QR + Tracking Info (135mm → 102mm) ──
        zone2_top = banner_y
        qr_size = 22 * mm
        qr_data = f"{carrier_tracking}|{recipient.get('name', '')}|{recipient.get('phone', '')}"
        qr_buffer = self._generate_qr_code(qr_data, size=70)
        qr_img = RLImage(qr_buffer, width=qr_size, height=qr_size)
        qr_img.drawOn(c, margin, zone2_top - qr_size - 3 * mm)

        text_x = margin + qr_size + 3 * mm
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(text_x, zone2_top - 8 * mm, carrier_tracking)

        if internal_tracking and internal_tracking != carrier_tracking:
            c.setFont("Helvetica", 7)
            c.setFillColor(colors.gray)
            c.drawString(text_x, zone2_top - 13 * mm, f"Ref: {internal_tracking}")

        c.setFont("Helvetica", 7)
        c.setFillColor(colors.gray)
        c.drawString(text_x, zone2_top - 18 * mm, datetime.now().strftime("%d/%m/%Y %H:%M"))

        # ── Separator ──
        sep1_y = zone2_top - 30 * mm
        c.setStrokeColor(colors.Color(0.85, 0.85, 0.85))
        c.setLineWidth(0.5)
        c.line(margin, sep1_y, A6_WIDTH - margin, sep1_y)

        # ── ZONE 3: Recipient (102mm → 55mm) ──
        y = sep1_y - 5 * mm
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margin, y, "DESTINATAIRE")

        y -= 6 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, recipient.get('name', 'N/A')[:32])

        y -= 5 * mm
        c.setFont("Helvetica", 9)
        c.drawString(margin, y, f"Tel: {recipient.get('phone', 'N/A')}")

        y -= 7 * mm
        c.setFillColor(carrier_color)
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(A6_WIDTH / 2, y, recipient.get('wilaya', 'N/A').upper())

        y -= 5 * mm
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawCentredString(A6_WIDTH / 2, y, recipient.get('commune', ''))

        y -= 5 * mm
        c.setFont("Helvetica", 8)
        address = recipient.get('address', '')[:55]
        c.drawCentredString(A6_WIDTH / 2, y, address)

        # ── Separator ──
        y -= 4 * mm
        c.setStrokeColor(colors.Color(0.85, 0.85, 0.85))
        c.line(margin, y, A6_WIDTH - margin, y)

        # ── ZONE 4: COD Amount (55mm → 30mm) ──
        y -= 5 * mm
        c.setFillColor(colors.HexColor('#DC3545'))
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(A6_WIDTH / 2, y, "MONTANT A ENCAISSER")

        y -= 10 * mm
        c.setFont("Helvetica-Bold", 26)
        cod_text = f"{cod_amount:,.0f} DA".replace(',', ' ')
        c.drawCentredString(A6_WIDTH / 2, y, cod_text)

        # ── Separator ──
        y -= 5 * mm
        c.setStrokeColor(colors.Color(0.85, 0.85, 0.85))
        c.line(margin, y, A6_WIDTH - margin, y)

        # ── ZONE 5: Barcode + Footer (30mm → 0mm) ──
        barcode_y = y - 16 * mm
        try:
            self._draw_barcode(c, carrier_tracking, 15 * mm, max(barcode_y, 8 * mm))
        except Exception:
            pass

        c.setFillColor(colors.gray)
        c.setFont("Helvetica", 6)
        c.drawCentredString(A6_WIDTH / 2, 2 * mm, f"Beyond Express - {datetime.now().strftime('%Y')}")

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
