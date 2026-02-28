#!/bin/bash
# Wrapper para ejecutar WiFi-BF con venv y sudo
# Uso: ./wifi_bf.sh -i wlan0 --scan

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Entorno virtual no encontrado."
    echo "Ejecuta primero: sudo bash setup_linux.sh"
    exit 1
fi

# Ejecutar con sudo y el Python del venv
sudo "$VENV_PYTHON" "$SCRIPT_DIR/wifi_bf.py" "$@"
