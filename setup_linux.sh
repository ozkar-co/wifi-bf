#!/bin/bash
# Script de instalación de WiFi-BF para WSL2/Linux
# Ejecutar con: sudo bash setup_linux.sh

set -e

echo "========================================"
echo "WiFi-BF Setup para WSL2/Linux"
echo "========================================"
echo ""

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
   echo "Este script debe ejecutarse con sudo"
   exit 1
fi

echo "[1/4] Actualizando lista de paquetes..."
apt-get update -qq

echo "[2/4] Instalando dependencias del sistema..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    aircrack-ng \
    wireless-tools \
    iw \
    git \
    build-essential

echo "[3/4] Configurando entorno virtual de Python..."
# Encontrar el usuario real (no root) para crear venv con permisos correctos
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Crear venv como usuario normal (no root)
echo "Creando entorno virtual..."
sudo -u "$REAL_USER" python3 -m venv "$SCRIPT_DIR/venv"

# Activar venv e instalar dependencias
echo "Instalando dependencias de Python en venv..."
sudo -u "$REAL_USER" bash -c "
    source '$SCRIPT_DIR/venv/bin/activate'
    pip install --upgrade pip setuptools wheel
    pip install -r '$SCRIPT_DIR/requirements.txt'
"

echo "  [OK] Entorno virtual creado en: $SCRIPT_DIR/venv"

echo "[4/4] Verificando instalación..."
echo ""
echo "Verificando herramientas necesarias:"

# Verificar aircrack-ng
if command -v aircrack-ng &> /dev/null; then
    echo "  [OK] aircrack-ng: $(aircrack-ng -h | head -1)"
else
    echo "  [ERROR] aircrack-ng no encontrado"
fi

# Verificar airodump-ng
if command -v airodump-ng &> /dev/null; then
    echo "  [OK] airodump-ng instalado"
else
    echo "  [ERROR] airodump-ng no encontrado"
fi

# Verificar airmon-ng
if command -v airmon-ng &> /dev/null; then
    echo "  [OK] airmon-ng instalado"
else
    echo "  [ERROR] airmon-ng no encontrado"
fi

# Verificar aireplay-ng
if command -v aireplay-ng &> /dev/null; then
    echo "  [OK] aireplay-ng instalado"
else
    echo "  [ERROR] aireplay-ng no encontrado"
fi

# Verificar Python
if command -v python3 &> /dev/null; then
    echo "  [OK] python3: $(python3 --version)"
else
    echo "  [ERROR] python3 no encontrado"
fi

echo ""
echo "========================================"
echo "Instalación completada"
echo "========================================"
echo ""
echo "IMPORTANTE: Se ha creado un entorno virtual en ./venv"
echo ""
echo "Dos formas de ejecutar WiFi-BF:"
echo ""
echo "Opción 1 - Usar el wrapper (recomendado):"
echo "  chmod +x wifi_bf.sh"
echo "  ./wifi_bf.sh -i wlan0 --scan"
echo ""
echo "Opción 2 - Llamar directamente al Python del venv:"
echo "  sudo venv/bin/python3 wifi_bf.py -i wlan0 --scan"
echo ""
echo "Para desarrollo (activar venv):"
echo "  source venv/bin/activate"
echo "  # Ahora puedes usar python3 normalmente"
echo ""
echo "Identificar interfaz WiFi: iwconfig"
echo ""
