import qrcode
from io import BytesIO

def generate_qr_code(data):
    """
    Genera un código QR a partir de los datos proporcionados.
    
    Args:
        data (str): Los datos para codificar en el QR.
    
    Returns:
        BytesIO: Un objeto BytesIO que contiene la imagen del código QR.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return img_io