"""
Configuración centralizada para WiFi-BF
"""
import os

# Directorios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
CHECKPOINT_DIR = os.path.join(LOG_DIR, "checkpoints")
WORDLIST_DIR = os.path.join(BASE_DIR, "wordlists")

# Crear directorios si no existen
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(WORDLIST_DIR, exist_ok=True)

# Configuración de logging
LOG_FILE = os.path.join(LOG_DIR, "wifi_bf.log")
LOG_LEVEL = "INFO"
LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Configuración de ejecución
MAX_THREADS = 4
CHECKPOINT_INTERVAL = 1000  # Cada cuántos intentos guardar checkpoint
VERBOSE = True
TIMEOUT_PER_ATTEMPT = 30  # segundos

# Configuración de fuerza bruta
BRUTE_FORCE_CHARSET = "0123456789"  # Solo números por defecto
BRUTE_FORCE_MIN_LENGTH = 4
BRUTE_FORCE_MAX_LENGTH = 16

# Configuración de diccionario
DICTIONARY_DEFAULT_PATH = os.path.join(WORDLIST_DIR, "common_passwords.txt")

# Configuración de reporte
SHOW_DECRYPTED_PASSWORD = False  # Si mostrar la contraseña en el reporte (seguridad)
REPORT_FORMAT = "text"  # "text", "json", "both"
REPORT_DIR = os.path.join(LOG_DIR, "reports")

os.makedirs(REPORT_DIR, exist_ok=True)
