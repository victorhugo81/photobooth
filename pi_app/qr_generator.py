import logging
from io import BytesIO

import qrcode
import qrcode.constants

logger = logging.getLogger(__name__)


def generate_qr(url: str, output_path: str) -> None:
    """Generate a QR code PNG pointing to *url* and save it to *output_path*."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
    logger.info("QR code saved to %s (url=%s)", output_path, url)


def generate_qr_bytes(url: str) -> BytesIO:
    """Generate a QR code PNG in memory and return a BytesIO buffer."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
