from flask import Blueprint, render_template, jsonify
from app.services.hotspot_service import start_hotspot, get_hotspot_credentials, get_dhcp_leases, stop_hotspot

hotspot_bp = Blueprint('hotspot', __name__)

@hotspot_bp.route("/hotspot", methods=["GET"])
def hotspot():
    # Iniciar el hotspot
    start_hotspot()

    # Obtener el SSID y la contraseña del hotspot
    ssid, password = get_hotspot_credentials()

    # Datos para el código QR
    qr_data = f"WIFI:S:{ssid};T:WPA;P:{password};;"

    # Renderizar la plantilla con los datos
    return render_template("hotspot.html", ssid=ssid, password=password, qr_data=qr_data)

@hotspot_bp.route("/api/hotspot/leases", methods=["GET"])
def dhcp_leases():
    """
    Endpoint que devuelve los leases de dnsmasq.
    """
    leases = get_dhcp_leases()
    return jsonify(leases)

@hotspot_bp.route("/api/hotspot/stop", methods=["POST"])
def hotspot_stop():
    stop_hotspot()

@hotspot_bp.route("/portal", methods=["GET"])
def portal():
    return render_template("portal.html")

@hotspot_bp.route("/connect", methods=["GET"])
def connect():
    return render_template("connect.html")