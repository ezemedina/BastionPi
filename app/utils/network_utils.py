import subprocess
import re

def get_interface_status(interface):
    """
    Verifica si una interfaz de red está conectada (UP) o desconectada (DOWN).
    
    Args:
        interface (str): Nombre de la interfaz de red (por ejemplo, "eth0" o "wlan0").
    
    Returns:
        bool: True si la interfaz está UP, False si está DOWN o si ocurre un error.
    """
    try:
        result = subprocess.run(
            ["ip", "link", "show", interface], 
            capture_output=True, 
            text=True
        )
        # Busca el estado de la interfaz (UP o DOWN)
        status_line = re.search(r"state (UP|DOWN)", result.stdout)
        if status_line:
            return status_line.group(1) == "UP"  # True si está UP, False si está DOWN
        else:
            return False  # Si no se encuentra el estado, asumimos que está DOWN
    except Exception as e:
        return False  # Error al ejecutar el comando

def get_interface_ip(interface):
    """
    Obtiene la IPv4 de una interfaz de red usando el comando `ip`.
    
    Args:
        interface (str): Nombre de la interfaz de red (por ejemplo, "eth0" o "wlan0").
    
    Returns:
        str: La dirección IPv4 de la interfaz, o None si no se encuentra o ocurre un error.
    """
    try:
        result = subprocess.run(
            ["ip", "-4", "addr", "show", interface], 
            capture_output=True, 
            text=True
        )
        # Busca la línea que contiene la IP
        ip_line = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", result.stdout)
        if ip_line:
            return ip_line.group(1)  # Devuelve la IPv4
        else:
            return None  # No se encontró una IP
    except Exception as e:
        return None  # Error al ejecutar el comando

def get_wifi_signal_strength():
    """
    Obtiene la fuerza de la señal WiFi y la normaliza en un rango de 0 a 4.
    
    Returns:
        int: Fuerza de la señal en una escala de 0 (muy baja) a 4 (muy alta).
    """
    try:
        result = subprocess.run(
            ["sudo", "iwconfig", "wlan0"], 
            capture_output=True, 
            text=True
        )
        # Busca la línea que contiene la fuerza de la señal
        signal_line = re.search(r"Signal level=(-?\d+)", result.stdout)
        if signal_line:
            signal_strength = int(signal_line.group(1))  # Obtiene el valor en dBm
            # Normaliza la señal en un rango de 0 a 4
            if signal_strength >= -50:
                return 4  # Full
            elif signal_strength >= -60:
                return 3  # Alto
            elif signal_strength >= -70:
                return 2  # Medio
            elif signal_strength >= -80:
                return 1  # Bajo
            else:
                return 0  # Muy bajo o desconectado
        else:
            return 0  # No se encontró la señal (desconectado)
    except Exception as e:
        return 0  # Error al obtener la señal

def get_wifi_ssid():
    """
    Obtiene el SSID de la red WiFi conectada.
    
    Returns:
        str: El SSID de la red WiFi, o None si no se encuentra o ocurre un error.
    """
    try:
        result = subprocess.run(
            ["sudo", "iwgetid", "-r"], 
            capture_output=True, 
            text=True
        )
        ssid = result.stdout.strip()  # Elimina espacios en blanco y saltos de línea
        return ssid if ssid else None
    except Exception as e:
        return None  # Error al obtener el SSID

def check_internet_access():
    """
    Verifica si hay acceso a Internet.
    
    Returns:
        bool: True si hay acceso a Internet, False si no hay acceso o ocurre un error.
    """
    try:
        # Intenta hacer ping a un servidor confiable (por ejemplo, Google DNS)
        result = subprocess.run(
            ["ping", "-c", "1", "8.8.8.8"], 
            capture_output=True, 
            text=True
        )
        return result.returncode == 0  # True si el ping fue exitoso
    except Exception as e:
        return False  # Error al ejecutar el comando

def get_eth_status():
    """
    Obtiene el estado de la interfaz Ethernet (eth0).
    
    Returns:
        dict: Un diccionario con el estado de la interfaz Ethernet.
              Ejemplo: {"connected": True, "ip": "192.168.1.100"}
    """
    eth_connected = get_interface_status("eth0")
    eth_ip = get_interface_ip("eth0") if eth_connected else None
    return {
        "connected": eth_connected,
        "ip": eth_ip
    }

def get_wifi_status():
    """
    Obtiene el estado de la interfaz WiFi (wlan0).
    
    Returns:
        dict: Un diccionario con el estado de la interfaz WiFi.
              Ejemplo: {"connected": True, "ip": "192.168.1.101", "signal_strength": 3, "ssid": "MiRedWiFi"}
    """
    wifi_connected = get_interface_status("wlan0")
    wifi_ip = get_interface_ip("wlan0") if wifi_connected else None
    signal_strength = get_wifi_signal_strength() if wifi_connected else 0
    ssid = get_wifi_ssid() if wifi_connected else None
    return {
        "connected": wifi_connected,
        "ip": wifi_ip,
        "signal_strength": signal_strength,
        "ssid": ssid
    }

def get_wireguard_status():
    """
    Obtiene el estado de WireGuard y la IP de la interfaz WireGuard.
    
    Returns:
        dict: Un diccionario con el estado de WireGuard.
              Ejemplo: {"connected": True, "ip": "10.8.0.2"}
    """
    try:
        # Verifica si WireGuard está activo
        result = subprocess.run(
            ["sudo", "wg"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            # Obtiene el nombre de la interfaz de WireGuard (por ejemplo, "wg0")
            interface_name = "wg0"  # Cambia esto si tu interfaz tiene otro nombre
            
            # Verifica si la interfaz de WireGuard está UP y tiene una IP asignada
            wg_connected = get_interface_status(interface_name)
            wg_ip = get_interface_ip(interface_name) if wg_connected else None
            
            # Solo se considera conectado si la interfaz está UP y tiene una IP asignada
            if wg_connected and wg_ip:
                return {
                    "connected": True,
                    "ip": wg_ip
                }
            else:
                return {
                    "connected": False,
                    "ip": None
                }
        else:
            # Si el comando `wg` falla, WireGuard no está activo
            return {
                "connected": False,
                "ip": None
            }
    except Exception as e:
        # Si ocurre un error, asumimos que WireGuard no está conectado
        return {
            "connected": False,
            "ip": None
        }