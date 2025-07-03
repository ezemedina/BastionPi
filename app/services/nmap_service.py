import subprocess
import os
from datetime import datetime
from typing import Optional
import requests
from ..models import CVE
from .. import db
from config import Config
import xml.etree.ElementTree as ET

# Diccionario para almacenar los procesos de nmap en ejecución
nmap_processes = {}

def get_cves_for_service(service_name, service_version):
    """Obtiene CVEs desde la base de datos o la API."""
    # Buscar CVEs en la base de datos
    cves = CVE.query.filter_by(service_name=service_name, service_version=service_version).all()
    if cves:
        return [{'cve_id': cve.cve_id, 'summary': cve.summary} for cve in cves]

    # Si no hay CVEs, consultar la API y guardar en la base de datos
    url = f"https://cve.circl.lu/api/search/{service_name}/{service_version}"
    response = requests.get(url)
    if response.status_code == 200:
        cves_from_api = response.json()
        for cve in cves_from_api:
            new_cve = CVE(
                service_name=service_name,
                service_version=service_version,
                cve_id=cve['id'],
                summary=cve['summary']
            )
            db.session.add(new_cve)
        db.session.commit()
        return cves_from_api
    return []

def parse_nmap_xml(filepath):
    """Parsea un archivo XML de Nmap y devuelve la información del escaneo."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        scan_info = {
            'filename': os.path.basename(filepath),
            'start_time': root.find('runstats/finished').attrib['timestr'],
            'scan_type': root.attrib['scanner'],
            'nmap_command': root.attrib['args'],
            'hosts': []
        }
        for host in root.findall('host'):
            host_info = {
                'ip': host.find('address').attrib['addr'],
                'ports': []
            }
            for port in host.findall('ports/port'):
                port_info = {
                    'port': port.attrib['portid'],
                    'state': port.find('state').attrib['state'],
                    'service': port.find('service').attrib['name'],
                    'service_version': port.find('service').attrib.get('version', 'unknown'),
                    'cves': []  # Inicializar lista de CVEs
                }
                # Obtener CVEs para el servicio y versión
                service_name = port_info['service']
                service_version = port_info['service_version']
                port_info['cves'] = get_cves_for_service(service_name, service_version)
                host_info['ports'].append(port_info)
            scan_info['hosts'].append(host_info)
        return scan_info
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None

def generate_netview(scan_info):
    """Genera una vista de red basada en los hosts y puertos escaneados."""
    netview = {
        'nodes': [],
        'links': []
    }
    hosts = scan_info.get('hosts', [])
    for host in hosts:
        netview['nodes'].append({'id': host['ip'], 'label': host['ip']})
        for port in host['ports']:
            if port['state'] == 'open':
                netview['links'].append({
                    'source': host['ip'],
                    'target': f"{host['ip']}:{port['port']}",
                    'label': port['service']
                })
    return netview

def start_nmap_listener(port: int) -> Optional[str]:
    """
    Inicia una prueba de conexión con nmap en el puerto especificado.
    """
    if port in nmap_processes:
        return f"El puerto {port} ya está en uso."

    try:
        # Comando para escanear el puerto con nmap
        command = ["sudo", "nmap", "-p", str(port), "localhost"]
        
        # Ejecutar el comando en segundo plano
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Almacenar el proceso en el diccionario
        nmap_processes[port] = process
        
        # Verificar si el puerto está abierto
        stdout, stderr = process.communicate(timeout=10)  # Esperar 10 segundos para la salida
        if "open" in stdout:
            return f"Prueba de conexión con nmap iniciada en el puerto {port}. Puerto abierto."
        else:
            return f"Prueba de conexión con nmap iniciada en el puerto {port}. Puerto cerrado."
    except subprocess.TimeoutExpired:
        # Si el proceso no termina en 10 segundos, asumimos que el puerto está cerrado
        return f"Prueba de conexión con nmap iniciada en el puerto {port}. Puerto cerrado (timeout)."
    except Exception as e:
        return f"Error al iniciar nmap: {e}"

def stop_nmap_listener(port: int) -> Optional[str]:
    """
    Detiene la prueba de conexión con nmap en el puerto especificado.
    """
    if port not in nmap_processes:
        return f"No hay una prueba de conexión con nmap en el puerto {port}."

    try:
        # Terminar el proceso de nmap
        process = nmap_processes[port]
        process.terminate()
        process.wait(timeout=5)  # Esperar a que el proceso termine
        
        # Eliminar el proceso del diccionario
        del nmap_processes[port]
        return f"Prueba de conexión con nmap en el puerto {port} detenida."
    except subprocess.TimeoutExpired:
        # Si el proceso no termina en 5 segundos, forzar su terminación
        process.kill()
        del nmap_processes[port]
        return f"Prueba de conexión con nmap en el puerto {port} detenida (forzada)."
    except Exception as e:
        return f"Error al detener nmap: {e}"

def generate_output_file(target, permanent=False):
    """
    Genera el nombre del archivo XML según la estructura: <timestamp>-<host_o_rango>-<permanent>.xml
    """
    timestamp = datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
    target_name = target.replace("/", "_")
    permanent_suffix = "-permanent" if permanent else ""
    filename = f"{timestamp}-{target_name}{permanent_suffix}.xml"
    return os.path.join(Config.NMAP_XML_PATH, filename)  # Usar Config.NMAP_XML_PATH

def run_nmap_command(command):
    """
    Ejecuta un comando de nmap con sudo.
    """
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def generate_output_file(target, scan_type, permanent=False):
    """
    Genera el nombre del archivo XML según la estructura: <timestamp>-<host_o_rango>-<scan_type>-<permanent>.xml
    """
    timestamp = datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
    target_name = target.replace("/", "_")
    permanent_suffix = "-permanent" if permanent else ""
    filename = f"{timestamp}-{target_name}-{scan_type}{permanent_suffix}.xml"
    return os.path.join(Config.NMAP_XML_PATH, filename)  # Usar Config.NMAP_XML_PATH

def run_nmap_command(command):
    """
    Ejecuta un comando de nmap con sudo.
    """
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def scan_target(target, scan_type, permanent=False):
    """
    Realiza un escaneo de un objetivo (host o rango de red) según el tipo de escaneo especificado.
    """
    output_file = generate_output_file(target, scan_type, permanent)
    
    # Definir los argumentos de nmap según el tipo de escaneo
    if scan_type == "quick":
        arguments = ["-F"]  # Escaneo rápido (puertos comunes)
    elif scan_type == "full":
        arguments = ["-p-"]  # Escaneo completo (todos los puertos)
    elif scan_type == "vuln":
        arguments = ["-A", "--script", "vuln"]  # Escaneo completo con vulnerabilidades
    else:
        return None, "Tipo de escaneo no válido."

    # Comando para escanear con sudo
    command = ["sudo", "nmap", "-sV", "-oX", output_file] + arguments + [target]
    
    success, output = run_nmap_command(command)
    if success:
        return output_file, None
    else:
        return None, output