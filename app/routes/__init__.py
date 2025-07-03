from .status_routes import status_bp
from .wifi_routes import wifi_bp
from .hotspot_routes import hotspot_bp
from .qr_routes import qr_bp
from .power_routes import power_bp
#from .nmap_routes import nmap_bp

__all__ = ["status_bp", "wifi_bp", "hotspot_bp", "qr_bp", "power_bp", "nmap_bp"]
