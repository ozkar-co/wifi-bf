"""
Configuración centralizada para WiFi-BF
Herramienta educativa para cracking de redes WiFi WPA/WPA2
Compatible con: Linux, WSL2 (requiere aircrack-ng)
"""
import os
import platform

# Directorios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
CHECKPOINT_DIR = os.path.join(LOG_DIR, "checkpoints")
WORDLIST_DIR = os.path.join(BASE_DIR, "wordlists")
CAPTURE_DIR = os.path.join(LOG_DIR, "captures")  # Captures de PCAP
HANDSHAKE_DIR = os.path.join(CAPTURE_DIR, "handshakes")

# Crear directorios si no existen
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(WORDLIST_DIR, exist_ok=True)
os.makedirs(CAPTURE_DIR, exist_ok=True)
os.makedirs(HANDSHAKE_DIR, exist_ok=True)

# Configuración de logging
LOG_FILE = os.path.join(LOG_DIR, "wifi_bf.log")
LOG_LEVEL = "INFO"
LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Configuración del sistema
SYSTEM_OS = platform.system()  # Linux, Windows, Darwin
IS_LINUX = SYSTEM_OS == "Linux"
IS_WSL = "microsoft" in platform.uname().release.lower() if IS_LINUX else False

# Configuración de ejecución
MAX_THREADS = 4
CHECKPOINT_INTERVAL = 1000  # Cada cuántos intentos guardar checkpoint
VERBOSE = True
TIMEOUT_PER_ATTEMPT = 30  # segundos

# Configuración de WiFi y captura
WLAN_INTERFACE = None  # Se debe especificar (ej: wlan0, wlan1)
MONITOR_MODE_TIMEOUT = 60  # segundos hasta timeout en monitor mode
DEAUTH_PACKETS = 10  # Paquetes de desautenticación para forzar handshake
CAPTURE_TIMEOUT = 120  # Tiempo máximo de captura en segundos
MIN_SIGNAL_STRENGTH = -60  # dBm (entre -100 a 0, más alto = más fuerte)

# Configuración de fuerza bruta
BRUTE_FORCE_CHARSET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
BRUTE_FORCE_MIN_LENGTH = 8  # WPA2 mínimo 8 caracteres
BRUTE_FORCE_MAX_LENGTH = 63  # WPA2 máximo 63 caracteres
BRUTE_FORCE_START_CHARSET = "abcdefghijklmnopqrstuvwxyz0123456789"  # Inicio más probable

# Configuración de diccionario
DICTIONARY_DEFAULT_PATH = os.path.join(WORDLIST_DIR, "common_passwords.txt")
DICTIONARY_WORDLIST_PATHS = [
    os.path.join(WORDLIST_DIR, "common_passwords.txt"),
    os.path.join(WORDLIST_DIR, "rockyou_top1000.txt"),  # Si existe
]

# Configuración de heurístico
HEURISTIC_MUTATIONS = [
    {"transform": "capitalize"},  # Test -> Test
    {"transform": "number_append", "range": (2000, 2026)},  # test -> test2025
    {"transform": "common_replacements"},  # test -> t3st (3=e, 0=o, etc)
]

# Configuración de WPA/WPA2 (PBKDF2)
WPA_ITERATIONS = 4096  # Estándar WPA
WPA_HASH_TYPE = "sha1"  # WPA/WPA2 usa HMAC-SHA1
WPA_PMKID_CAPTURE = False  # Intentar capturar PMKID (más rápido)

# Configuración de reporte
SHOW_DECRYPTED_PASSWORD = False  # Si mostrar la contraseña en el reporte (seguridad)
REPORT_FORMAT = "text"  # "text", "json", "both"
REPORT_DIR = os.path.join(LOG_DIR, "reports")

os.makedirs(REPORT_DIR, exist_ok=True)

# Herramientas externas
AIRCRACK_NG_PATH = "/usr/bin/aircrack-ng"
AIRODUMP_NG_PATH = "/usr/bin/airodump-ng"
AIRMON_NG_PATH = "/usr/bin/airmon-ng"
AIREPLAY_NG_PATH = "/usr/bin/aireplay-ng"
