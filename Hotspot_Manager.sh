#!/bin/bash

WIFI_INTERFACE="wlan0"

check_wlan0() {
    if ! ip link show "$WIFI_INTERFACE" | grep -q "UP"; then
        ip link set "$WIFI_INTERFACE" up
        sleep 2  # Give it time to initialize
    fi

    # Assign static IP if not set
    if ! ip addr show "$WIFI_INTERFACE" | grep -q "192.168.4.1"; then
        ip addr flush dev "$WIFI_INTERFACE"
        ip addr add 192.168.4.1/24 dev "$WIFI_INTERFACE"
    fi
}

start_hotspot() {

    # Stop NetworkManager and wpa_supplicant to avoid conflicts
    systemctl stop NetworkManager
    systemctl stop wpa_supplicant

    # Ensure wlan0 is up before starting hostapd
    check_wlan0

    # Restart services
    systemctl start dnsmasq
    systemctl start hostapd
}

check_wifi_connection() {
    local ssid="$1"
    local retries=5
    local wait_time=5

    echo "Checking WiFi connection to SSID: $ssid..."

    for ((i=1; i<=retries; i++)); do
        # Check if wlan0 has an IP address
        if ip addr show "$WIFI_INTERFACE" | grep -q "inet "; then
            # Check connectivity by pinging a reliable host (e.g., Google DNS)
            if ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
                echo "WiFi connection established successfully."
                return 0
            else
                echo "No internet connectivity. Retrying... ($i/$retries)"
            fi
        else
            echo "No IP address assigned. Retrying... ($i/$retries)"
        fi
        sleep "$wait_time"
    done

    echo "Failed to establish WiFi connection after $retries attempts."
    return 1
}

stop_hotspot() {
    WIFI_SSID=$1
    WIFI_PASSWORD=$2

    if [ -z "$WIFI_SSID" ] || [ -z "$WIFI_PASSWORD" ]; then
        echo "Usage: $0 stop <WiFi_SSID> <WiFi_PASSWORD>"
        exit 1
    fi

    # Stop hotspot services
    systemctl stop hostapd
    systemctl stop dnsmasq

    # Reset wlan0
    ip addr flush dev "$WIFI_INTERFACE"

    # Restart NetworkManager and wpa_supplicant
    systemctl start wpa_supplicant
    systemctl start NetworkManager

    sleep 10
    # Connect to specified WiFi
    nmcli dev wifi connect "$WIFI_SSID" password "$WIFI_PASSWORD"
    rm -rf /var/lib/misc/dnsmasq.leases

    # Check WiFi connection
    if ! check_wifi_connection "$WIFI_SSID"; then
        echo "Failed to connect to WiFi. Restarting hotspot..."
        start_hotspot
    else
        echo "WiFi connection successful. Exiting."
    fi
}

case "$1" in
    start)
        start_hotspot
        ;;
    stop)
        stop_hotspot "$2" "$3"
        ;;
    *)
        echo "Usage: $0 start | stop <WiFi_SSID> <WiFi_PASSWORD>"
        exit 1
        ;;
esac
