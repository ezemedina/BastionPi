from flask import Blueprint, send_file
from app.services.qr_service import generate_qr_code

qr_bp = Blueprint('qr', __name__)

@qr_bp.route("/api/qr/<data>", methods=["GET"])
def get_qr(data):
    """
    Genera un código QR a partir de los datos proporcionados.
    
    Args:
        data (str): Los datos para codificar en el QR.
    
    Returns:
        Response: La imagen del código QR.
    """
    qr_code = generate_qr_code(data)
    return send_file(qr_code, mimetype='image/png')