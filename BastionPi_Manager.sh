#!/bin/bash

# Global variables
APP_DIR=$(dirname "$(realpath "$0")")  # Get the directory where the script is located
HOSTAPD_CONF="/etc/hostapd/hostapd.conf"
DNSMASQ_CONF="/etc/dnsmasq.conf"
PID_DIR="/run/bastionpi"
WLAN_INTERFACE="wlan0"
ETH_INTERFACE="eth0"
LOG_FILE="$APP_DIR/app.log"  # Log file in the project directory
DOCKER_COMPOSE_VERSION="2.20.2"
PORTAINER_VERSION="2.21.5"
HOTSPOT_IP_RANGE="192.168.4.10 - 192.168.4.100"
SSID="BastionPi"

# Check if the operating system is Debian or Raspbian
if ! grep -q 'ID=debian' /etc/os-release ; then
    echo "This script is designed for Debian-based systems only."
    exit 1
fi

# Check if the script is run with sudo privileges
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo."
    exit 1
fi

# Generate a random WPA key
generate_wpa_key() {
    tr -dc 'A-Za-z0-9!?%=' < /dev/urandom | head -c 12
}

# Get the active IP address
get_active_ip() {
    local ip=""
    # Try to get the IP from the WiFi interface
    ip=$(ip -4 addr show "$WLAN_INTERFACE" 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
    if [ -z "$ip" ]; then
        # If no IP on WiFi, try the Ethernet interface
        ip=$(ip -4 addr show "$ETH_INTERFACE" 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
    fi
    echo "$ip"
}

# Regenerate WPA key and update hostapd.conf
regenerate_wpa_key() {
    echo "Regenerating WPA key..."
    local new_wpa_key=$(generate_wpa_key)
    sed -i "s/^wpa_passphrase=.*/wpa_passphrase=$new_wpa_key/" $HOSTAPD_CONF
    echo "New WPA key generated: $new_wpa_key"
}

# Installation function
install() {
    echo "Starting installation..."
    
    # Check if the WLAN interface exists
    echo -n "Checking if the interface $WLAN_INTERFACE exists... "
    if ! ip link show "$WLAN_INTERFACE" > /dev/null 2>&1; then
        echo "Error: The interface $WLAN_INTERFACE does not exist."
        exit 1
    fi
    echo "OK"

    # Update packages and install dependencies
    echo "Updating packages..."
    apt update
    echo "Installing dependencies..."
    apt install -y hostapd dnsmasq python3-full wireguard
    systemctl unmask hostapd

    # Configure hostapd and dnsmasq
    echo "Configuring hostapd and dnsmasq..."
    local initial_wpa_key=$(generate_wpa_key)
    cat > $HOSTAPD_CONF <<EOL
interface=$WLAN_INTERFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=7
wpa=2
wpa_passphrase=$initial_wpa_key
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOL
    
    cat > $DNSMASQ_CONF <<EOL
interface=$WLAN_INTERFACE
dhcp-range=192.168.4.10,192.168.4.100,12h
dhcp-option=3,192.168.4.1
dhcp-option=6,8.8.8.8,8.8.4.4
EOL

    # Install Docker
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
    rm get-docker.sh

    # Install Docker Compose
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    # Configure Portainer
    echo "Configuring Portainer..."
    docker volume create portainer_data
    docker run -d -p 8000:8000 -p 9443:9443 --name portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:$PORTAINER_VERSION

    # Install the Python application
    echo "Installing the Python application..."
    python3 -m venv "$APP_DIR/BastionPi"
    source "$APP_DIR/BastionPi/bin/activate"
    pip install -r "$APP_DIR/requirements.txt" || {
        echo "Error installing Python dependencies."
        exit 1
    }

    # Configure autostart
    echo "Configuring autostart..."
    cat > /etc/xdg/lxsession/LXDE-pi/autostart <<EOL
@/usr/bin/sudo /bin/bash $APP_DIR/BastionPi_Manager.sh start
EOL

    # Final report
    echo "----------------------------------------"
    echo "Installation completed."
    echo "Installation summary:"
    echo ""
    echo "Installed packages:"
    echo "  - Hostapd"
    echo "  - Dnsmasq"
    echo "  - WireGuard"
    echo "  - Docker"
    echo "  - Docker Compose (version: $DOCKER_COMPOSE_VERSION)"
    echo ""
    echo "Hotspot configuration:"
    echo "  - SSID: $SSID"
    echo "  - Initial WPA key: $initial_wpa_key"
    echo "  - IP range: $HOTSPOT_IP_RANGE"
    echo "----------------------------------------"
}

# Start the application
start_app() {
    echo "Starting the application..."
    mkdir -p $PID_DIR

    # Regenerate WPA key
    regenerate_wpa_key

    # Wait until LXDE is running
    echo "Waiting for LXDE to start..."
    local max_retries=10
    local retries=0
    until pgrep -x "lxsession" > /dev/null; do
        echo "LXDE is not running yet... ($((retries + 1))/$max_retries)"
        sleep 2
        retries=$((retries + 1))
        if [ $retries -ge $max_retries ]; then
            echo "LXDE did not start. Please start the LXDE environment manually and try again."
            exit 1
        fi
    done
    echo "LXDE is running."

    # Start the Python application
    echo "Starting Python application..."
    source "$APP_DIR/BastionPi/bin/activate"
    nohup python3 "$APP_DIR/run.py" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_DIR/python_app.pid"

    # Wait for the Python application to start
    sleep 5

    # Start Chromium in kiosk mode
    echo "Starting Chromium..."
    export DISPLAY=:0
    nohup sudo -u $(logname) chromium-browser --kiosk http://localhost:5000 > /dev/null 2>&1 &
    echo $! > "$PID_DIR/chromium.pid"

    echo "Application started. PIDs saved in $PID_DIR."
}

# Stop the application
stop_app() {
    echo "Stopping the application..."
    if [ -f "$PID_DIR/python_app.pid" ]; then
        kill $(cat "$PID_DIR/python_app.pid") && rm "$PID_DIR/python_app.pid"
    fi
    if [ -f "$PID_DIR/chromium.pid" ]; then
        kill $(cat "$PID_DIR/chromium.pid") && rm "$PID_DIR/chromium.pid"
    fi
}

# Restart the application
restart_app() {
    echo "Restarting the application..."
    stop_app
    start_app
}

# Uninstall function
uninstall() {
    echo "Starting uninstallation..."

    # Stop the application
    echo "Stopping the application..."
    stop_app

    # Remove hostapd and dnsmasq configurations
    echo "Removing hostapd and dnsmasq configurations..."
    rm -f $HOSTAPD_CONF $DNSMASQ_CONF

    # Remove Docker and Portainer
    echo "Removing Docker and Portainer..."
    docker stop portainer && docker rm portainer
    docker volume rm portainer_data
    apt remove --purge -y docker docker.io containerd runc

    # Remove Python virtual environment
    echo "Removing Python virtual environment..."
    rm -rf "$APP_DIR/venv"

    # Remove autostart configuration
    echo "Removing autostart configuration..."
    sed -i "\|$APP_DIR/BastionPi_Manager.sh start|d" /etc/xdg/lxsession/LXDE-pi/autostart

    # Remove PID directory
    echo "Removing PID directory..."
    rm -rf $PID_DIR

    # Remove installed packages
    echo "Removing installed packages..."
    apt remove --purge -y hostapd dnsmasq python3-full wireguard
    apt autoremove -y

    echo "----------------------------------------"
    echo "Uninstallation completed."
    echo "All components have been removed."
    echo "----------------------------------------"
}

# Main menu
case "$1" in
    install) install ;;
    uninstall) uninstall ;;
    start) start_app ;;
    stop) stop_app ;;
    restart) restart_app ;;
    *) echo "Usage: $0 {install|uninstall|start|stop|restart}" ; exit 1 ;;
esac
