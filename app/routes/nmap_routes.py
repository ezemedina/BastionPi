from flask import Blueprint, request, jsonify
from app.services.nmap_service import scan_target, start_nmap_listener, stop_nmap_listener
import uuid

nmap_bp = Blueprint('nmap', __name__)

@nmap_bp.route('/api/nmap/scan_network', methods=['POST'])
def scan_network_route():
    data = request.json
    ip_range = data.get('ip_range')
    scan_type = data.get('scan_type', 'quick')  # Por defecto, escaneo rápido
    permanent = data.get('permanent', False)
    
    if not ip_range:
        return jsonify({"error": "Se requiere el parámetro 'ip_range'"}), 400
    
    output_file, error = scan_target(ip_range, scan_type, permanent)
    if output_file:
        return jsonify({"message": "Escaneo de red completado", "file": output_file}), 202
    else:
        return jsonify({"error": f"Error al realizar el escaneo: {error}"}), 500

@nmap_bp.route('/api/nmap/scan_host', methods=['POST'])
def scan_host_route():
    data = request.json
    host = data.get('host')
    scan_type = data.get('scan_type', 'quick')  # Por defecto, escaneo rápido
    permanent = data.get('permanent', False)
    
    if not host:
        return jsonify({"error": "Se requiere el parámetro 'host'"}), 400
    
    output_file, error = scan_target(host, scan_type, permanent)
    if output_file:
        return jsonify({"message": "Escaneo de host completado", "file": output_file}), 202
    else:
        return jsonify({"error": f"Error al realizar el escaneo: {error}"}), 500

@nmap_bp.route('/api/nmap/full_scan', methods=['POST'])
def full_scan_route():
    data = request.json
    target = data.get('target')
    scan_type = data.get('scan_type', 'quick')  # Por defecto, escaneo rápido
    permanent = data.get('permanent', False)
    
    if not target:
        return jsonify({"error": "Se requiere el parámetro 'target'"}), 400
    
    output_file, error = scan_target(target, scan_type, permanent)
    if output_file:
        return jsonify({"message": "Escaneo completo completado", "file": output_file}), 202
    else:
        return jsonify({"error": f"Error al realizar el escaneo: {error}"}), 500
    
@nmap_bp.route('/api/nmap/<int:port>/listening', methods=['POST'])
def start_nc(port):
    result = start_nmap_listener(port)
    return jsonify({"message": result}), 202

# Ruta para detener una prueba de conexión con nmap
@nmap_bp.route('/api/nmap/<int:port>/close', methods=['POST'])
def stop_nc(port):
    result = stop_nmap_listener(port)
    return jsonify({"message": result}), 202