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
    aircrack-ng \
    wireless-tools \
    iw \
    git \
    build-essential

echo "[3/4] Instalando dependencias de Python..."
pip3 install -q -r requirements.txt

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
echo "Próximos pasos:"
echo "1. Identifica tu interfaz WiFi: iwconfig"
echo "2. Ejecuta: python3 wifi_bf.py --help"
echo "3. Ejemplo: python3 wifi_bf.py --interface wlan0 --scan"
echo ""
echo "Nota: La mayoría de comandos requieren privilegios de root (sudo)"
echo ""
