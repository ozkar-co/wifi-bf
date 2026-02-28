# WiFi-BF - Instalación Rápida

## Requisitos previos

- WSL2 con Ubuntu (o Linux nativo)
- Adaptador WiFi compatible con modo monitor
- Permisos de sudo

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/ozkar-co/wifi-bf.git
cd wifi-bf

# 2. Ejecutar script de instalación (instala todo + crea venv)
sudo bash setup_linux.sh

# 3. Dar permisos al wrapper
chmod +x wifi_bf.sh
```

## Uso básico

```bash
# Escanear redes disponibles
./wifi_bf.sh -i wlan0 --scan

# Atacar una red específica
./wifi_bf.sh -i wlan0 --attack "ESSID" "AA:BB:CC:DD:EE:FF"

# Ver ayuda
./wifi_bf.sh --help
```

## Uso alternativo (sin wrapper)

```bash
# Ejecutar directamente con el Python del venv
sudo venv/bin/python3 wifi_bf.py -i wlan0 --scan
```

## Solución de problemas

### "No such file or directory: venv/bin/python3"
```bash
# Reinstalar el entorno
sudo bash setup_linux.sh
```

### "Operation not permitted"
```bash
# Siempre usar sudo
sudo venv/bin/python3 wifi_bf.py ...
# O con el wrapper:
./wifi_bf.sh ...
```

### "Interface not found"
```bash
# Listar interfaces disponibles
iwconfig
# O
ip link show
```

## Documentación completa

- [README.md](README.md) - Descripción general
- [USAGE.md](USAGE.md) - Guía de uso detallada
- [SETUP_WSL2.md](SETUP_WSL2.md) - Instalación completa en WSL2
- [WIFI_REAL.md](WIFI_REAL.md) - Guía técnica de ataque

## Disclaimer

Solo usar en redes propias o con autorización explícita. El acceso no autorizado es ilegal.
