#!/bin/bash

# Default values
DEFAULT_PORT=8000

usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -u, --url URL            Set the firmware URL (default: http://<local-ip>:8000/firmware)"
    echo "  -s, --ssid SSID          Set the WiFi SSID"
    echo "  -p, --password PASSWORD  Set the WiFi password"
    echo "  -b, --board_id ID        Set the board ID"
    echo "  -h, --help               Display this help message"
    exit 1
}

get_local_ip() {
    ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d'/' -f1 | head -n 1
}

# Parse input arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -u|--url) FIRMWARE_URL="$2"; shift ;;
        -s|--ssid) SSID="$2"; shift ;;
        -p|--password) PASSWORD="$2"; shift ;;
        -b|--board_id) BOARD_ID="$2"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# Get local IP and set to default port if no url provided
if [ -z "$FIRMWARE_URL" ]; then
    LOCAL_IP=$(get_local_ip)
    FIRMWARE_URL="http://$LOCAL_IP:$DEFAULT_PORT/firmware"
fi

if [ -z "$SSID" ]; then
    read -p "Enter WiFi SSID: " SSID
fi

if [ -z "$PASSWORD" ]; then
    read -p "Enter WiFi Password: " PASSWORD
fi

if [ -z "$BOARD_ID" ]; then
    read -p "Enter Board ID: " BOARD_ID
fi

# Update config.py
if [ -f config.py ]; then
    sed -i "s|firmware_url = .*|firmware_url = \"$FIRMWARE_URL\"|" config.py
else
	echo "There is no config.py . Please create one with the following fields:"
	echo "firmware = {your firmware's name}"
	echo "version = {your firmware's version}"
	echo "firmware_url = {something that will be replaced}"
	echo "other_configuration_varibales..."
fi

# Write to secrets.py - note this can't work if secrets.py contains other secrets,
# do as above in that case
cat <<EOL > secrets.py
# This is a board-specific file
wifi = {
    "ssid": "$SSID",
    "password": "$PASSWORD",
}
board_id = "$BOARD_ID"
EOL

echo "Configuration updated successfully."

