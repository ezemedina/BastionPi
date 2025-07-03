from flask import Blueprint, jsonify, render_template, redirect, abort, request
from app.services.status_service import get_system_status, get_network_status, check_service_status, handle_service_action
from datetime import datetime

status_bp = Blueprint('status', __name__)


@status_bp.route("/", methods=["GET"])
def index():
    # Obtener la dirección IP del cliente
    client_ip = request.remote_addr

    # Redirigir según la IP
    if client_ip.startswith("192.168.4."):
        return redirect("/connect"), 302  # Redirigir a /connect
    elif client_ip == "127.0.0.1":
        return redirect("/raspi_display"), 302  # Redirigir a /raspi_display
    else:
        abort(404)  # Devolver un 404 para otras IPs

# Estado del sistema
@status_bp.route('/api/status/system', methods=['GET'])
def status_system():
    return jsonify(get_system_status())

# Estado de la red
@status_bp.route('/api/status/network', methods=['GET'])
def status_network():
    return jsonify(get_network_status())

# Estado de un servicio
@status_bp.route("/api/status/<service_name>", methods=["GET"])
def service_status(service_name):
    status = check_service_status(service_name)
    if status is None:
        return jsonify({"error": "Servicio no encontrado"}), 404
    return jsonify({"status": status})

@status_bp.route('/api/services/<service_name>/<action>', methods=['POST'])
def service_action(service_name, action):
    """
    Endpoint para manejar acciones sobre servicios.
    """
    if action not in ["restart", "stop", "start"]:
        return jsonify({"status": "error", "message": "Acción no válida. Use 'restart' o 'stop'."}), 400

    result = handle_service_action(service_name, action)
    if result["status"] == "error":
        return jsonify(result), 500
    return jsonify(result), 200

# Página de visualización de Raspberry Pi
@status_bp.route("/raspi_display", methods=["GET"])
def raspi_display():
    return render_template("raspi_display.html")