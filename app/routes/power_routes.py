from flask import Blueprint, jsonify
from app.services.power_service import power_action

power_bp = Blueprint('power', __name__)

@power_bp.route('/api/power/<action>', methods=['POST'])
def power(action):
    """
    Maneja las acciones de power (shutdown o reboot).
    """
    if action not in ["shutdown", "reboot"]:
        return jsonify({"error": "Acción no válida"}), 400

    result = power_action(action)
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result), 200