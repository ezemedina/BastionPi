from flask import Blueprint, jsonify, request
from app.services.wifi_service import scan_wifi_networks, connect_to_wifi

wifi_bp = Blueprint('wifi', __name__)

# Buscar redes WiFi
@wifi_bp.route("/api/wifi/search", methods=["GET"])
def wifi_search():
    """
    Endpoint que devuelve todas las redes WiFi en el área con su seguridad y fuerza de señal.
    """
    networks = scan_wifi_networks()
    return jsonify(networks)

# Conectar a una red WiFi
@wifi_bp.route("/api/wifi/connect", methods=["POST"])
def wifi_connect():
    """
    Endpoint que conecta a una red WiFi específica.
    - Recibe un JSON con 'ssid' y 'password'.
    """
    data = request.get_json()

    # Validar que se enviaron los parámetros correctos
    if not data or "ssid" not in data or "password" not in data:
        return jsonify({"error": "Missing SSID or password"}), 400

    ssid = data["ssid"]
    password = data["password"]

    # Intentar conectar a la red WiFi
    success, message = connect_to_wifi(ssid, password)
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 500