from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from config import Config

# Inicializar la aplicación Flask
app = Flask(__name__)
socketio = SocketIO(app)
CORS(app, origins=["*"])

# Cargar configuraciones
app.config.from_object(Config)

# Importar y registrar blueprints
from app.routes.status_routes import status_bp
from app.routes.wifi_routes import wifi_bp
from app.routes.hotspot_routes import hotspot_bp
from app.routes.qr_routes import qr_bp
from app.routes.power_routes import power_bp
#from app.routes.nmap_routes import nmap_bp

app.register_blueprint(status_bp)
app.register_blueprint(wifi_bp)
app.register_blueprint(hotspot_bp)
app.register_blueprint(qr_bp)
app.register_blueprint(power_bp)
#app.register_blueprint(nmap_bp)
