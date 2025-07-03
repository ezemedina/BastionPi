import os

class Config:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    NMAP_XML_PATH = os.path.join(SCRIPT_DIR, "nmap_scans")
    HOTSPOT_MANAGER = os.path.join(SCRIPT_DIR, "Hotspot_Manager.sh")
    DOCKER_SERVICES = ["portainer", "docmost", "guacamole", "nginx_proxy_manager"]
    SYSTEM_SERVICES = ["docker", "cockpit"]

# Crear el directorio para los escaneos de Nmap si no existe
os.makedirs(Config.NMAP_XML_PATH, exist_ok=True)