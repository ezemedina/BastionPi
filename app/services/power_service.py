import subprocess

def power_action(action):
    """
    Ejecuta una acción de power (shutdown o reboot).
    
    Args:
        action (str): La acción a ejecutar ("shutdown" o "reboot").
    
    Returns:
        dict: Un diccionario con el resultado de la acción.
    """
    try:
        if action == "shutdown":
            subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
            return {"message": "El sistema se está apagando..."}
        elif action == "reboot":
            subprocess.run(["sudo", "reboot"], check=True)
            return {"message": "El sistema se está reiniciando..."}
        else:
            return {"error": "Acción no válida"}, 400
    except subprocess.CalledProcessError as e:
        return {"error": f"Error al ejecutar la acción: {str(e)}"}, 500