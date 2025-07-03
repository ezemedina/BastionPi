import subprocess
import re
from config import Config

def start_hotspot():
    """
    Inicia el hotspot usando el script manage_hotspot.sh.
    """
    try:
        subprocess.run(["sudo", Config.HOTSPOT_MANAGER, "start"], check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error al iniciar el hotspot: {str(e)}")

def get_hotspot_credentials():
    """
    Lee el SSID y la contraseña del archivo de configuración de hostapd.
    
    Returns:
        tuple: (ssid, password)
    """
    try:
        with open("/etc/hostapd/hostapd.conf", "r") as f:
            content = f.read()

        # Extraer el SSID y la contraseña usando expresiones regulares
        ssid_match = re.search(r"ssid=(.*)", content)
        password_match = re.search(r"wpa_passphrase=(.*)", content)

        if ssid_match and password_match:
            return ssid_match.group(1), password_match.group(1)
        else:
            raise Exception("No se pudo leer el SSID o la contraseña del archivo de hostapd.")
    except Exception as e:
        raise Exception(f"Error al leer el archivo de hostapd: {str(e)}")

def get_dhcp_leases():
    """
    Lee los leases de dnsmasq y devuelve una lista de dispositivos conectados.
    
    Returns:
        list: Lista de leases con información de los dispositivos conectados.
    """
    try:
        with open("/var/lib/misc/dnsmasq.leases", "r") as f:
            leases = f.readlines()

        # Parsear los leases
        parsed_leases = []
        for lease in leases:
            parts = lease.strip().split()
            if len(parts) >= 4:
                parsed_leases.append({
                    "mac": parts[1],
                    "ip": parts[2],
                    "hostname": parts[3]
                })

        return parsed_leases
    except Exception as e:
        raise Exception(f"Error al leer los leases de dnsmasq: {str(e)}")
    
def stop_hotspot():
    """
    Inicia el hotspot usando el script manage_hotspot.sh.
    """
    try:
        subprocess.run(["sudo", Config.HOTSPOT_MANAGER, "stop"], check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error al iniciar el hotspot: {str(e)}")