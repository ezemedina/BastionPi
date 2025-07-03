import subprocess
import re
from config import Config

def scan_wifi_networks():
    """
    Escanea las redes WiFi disponibles y devuelve una lista con:
    - SSID (nombre de la red)
    - Seguridad (abierta o cerrada)
    - Fuerza de señal en escala de 1 a 4
    """
    try:
        # Ejecuta el escaneo de redes WiFi
        output = subprocess.check_output("sudo iwlist wlan0 scan", shell=True).decode()

        networks = []
        raw_networks = output.split("Cell")  # Divide la salida por cada red detectada

        for network in raw_networks:
            ssid_match = re.search(r'ESSID:"(.*?)"', network)
            encryption_match = re.search(r"Encryption key:(on|off)", network)
            signal_match = re.search(r"Signal level=(-?\d+) dBm", network)

            if ssid_match and encryption_match and signal_match:
                ssid = ssid_match.group(1)
                encryption = "closed" if encryption_match.group(1) == "on" else "open"
                signal_strength = int(signal_match.group(1))

                # Escala de fuerza de señal (1 a 4)
                strength_scale = 1 if signal_strength < -80 else 2 if signal_strength < -70 else 3 if signal_strength < -60 else 4

                networks.append({
                    "ssid": ssid,
                    "security": encryption,
                    "signal_strength": strength_scale
                })

        return networks

    except Exception as e:
        return {"error": str(e)}

def connect_to_wifi(ssid, password):
    """
    Conecta a una red WiFi específica usando el script HOTSPOT_MANAGER.
    
    Args:
        ssid (str): El SSID de la red WiFi.
        password (str): La contraseña de la red WiFi.
    
    Returns:
        tuple: (success, message)
            - success (bool): True si la conexión fue exitosa, False si no.
            - message (str): Mensaje descriptivo del resultado.
    """
    try:
        # Ejecutar el script HOTSPOT_MANAGER con los argumentos stop, ssid y password
        result = subprocess.run(
            ["sudo", Config.HOTSPOT_MANAGER, "stop", ssid, password],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True, f"Conectado a {ssid} exitosamente."
        else:
            return False, f"Error al conectar a {ssid}: {result.stderr}"
    except Exception as e:
        return False, f"Excepción al conectar a {ssid}: {str(e)}"