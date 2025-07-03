import psutil
import subprocess
import time
from app.utils.network_utils import get_eth_status, get_wifi_status, get_wireguard_status, check_internet_access
from config import Config

# Variables globales para almacenar la última medición de red
last_net_io = psutil.net_io_counters()
last_time = time.time()

# Variables globales para almacenar la última medición de red
last_net_io = psutil.net_io_counters()
last_time = time.time()

def get_system_status():
    """
    Obtiene el estado del sistema: CPU, memoria, disco y ancho de banda de red.
    """
    global last_net_io, last_time

    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Obtener estadísticas de red y calcular el ancho de banda utilizado
    current_net_io = psutil.net_io_counters()
    current_time = time.time()

    # Calcular la diferencia de bytes y tiempo
    bytes_sent_diff = current_net_io.bytes_sent - last_net_io.bytes_sent
    bytes_recv_diff = current_net_io.bytes_recv - last_net_io.bytes_recv
    time_diff = current_time - last_time

    # Calcular la tasa de transferencia en bytes por segundo
    upload_speed = bytes_sent_diff / time_diff  # Subida (upload)
    download_speed = bytes_recv_diff / time_diff  # Bajada (download)

    # Actualizar las variables globales para la próxima medición
    last_net_io = current_net_io
    last_time = current_time

    return {
        "cpu_usage": cpu_usage,
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent
        },
        "disks": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        },
        "network": {
            "upload_speed": upload_speed,  # Subida (upload)
            "download_speed": download_speed  # Bajada (download)
        }
    }

# Estado de la red
def get_network_status():
    """
    Obtiene el estado de la red: Ethernet, WiFi, VPN y acceso a Internet.
    """
    return {
        "eth": get_eth_status(),
        "wifi": get_wifi_status(),
        "vpn": get_wireguard_status(),
        "internet": check_internet_access()
    }

# Estado de los servicios
def check_service_status(service_name):
    """
    Verifica el estado de un servicio (Docker o del sistema).
    """
    if service_name in Config.DOCKER_SERVICES:
        return check_docker_service(service_name)
    elif service_name in Config.SYSTEM_SERVICES:
        return check_system_service(service_name)
    else:
        return None

def check_docker_service(service_name):
    """
    Verifica si un contenedor de Docker está corriendo.
    """
    if service_name == "docmost":
        output = subprocess.check_output("sudo docker ps --format '{{.Names}}'", shell=True).decode().strip()
        running_containers = output.split("\n")
        return "running" if "docmost-docmost-1" in running_containers else "stopped"
    else:
        try:
            output = subprocess.check_output("sudo docker ps --format '{{.Names}}'", shell=True).decode().strip()
            running_containers = output.split("\n")
            return "running" if service_name in running_containers else "stopped"
        except Exception:
            return "stopped"

def check_system_service(service_name):
    """
    Verifica si un servicio del sistema operativo está activo con systemctl.
    """
    if service_name == "cockpit":
        output = subprocess.check_output(f"sudo systemctl is-active {service_name}.socket", shell=True).decode().strip()
        return "running" if output == "active" else "stopped"
    else:
        try:
            output = subprocess.check_output(f"sudo systemctl is-active {service_name}", shell=True).decode().strip()
            return "running" if output == "active" else "stopped"
        except Exception:
            return "stopped"
        
def run_command(command):
    """
    Ejecuta un comando en el sistema y devuelve el resultado.
    """
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return {"status": "success", "message": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Error: {e.stderr}"}

def handle_service_action(service_name, action):
    """
    Maneja la acción (restart o stop) para un servicio.
    """
    if service_name in Config.DOCKER_SERVICES:
        # Comando para reiniciar o detener un contenedor de Docker
        if action == "restart":
            return run_command(["docker", "restart", service_name])
        elif action == "stop":
            return run_command(["docker", "stop", service_name])
        elif action == "stop":
            return run_command(["docker", "start", service_name])
    elif service_name in Config.SYSTEM_SERVICES:
        # Comando para reiniciar o detener un servicio del sistema
        if action == "restart":
            return run_command(["sudo", "systemctl", "restart", service_name])
        elif action == "stop":
            return run_command(["sudo", "systemctl", "stop", service_name])
        elif action == "start":
            return run_command(["sudo", "systemctl", "start", service_name])
    else:
        return {"status": "error", "message": f"Servicio {service_name} no reconocido."}