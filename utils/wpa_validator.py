"""
Módulo de validación WPA/WPA2
Valida contraseñas contra handshakes capturados usando PBKDF2
"""
import hmac
import hashlib
import subprocess
import os
import tempfile
import config
from utils.logger import get_logger

logger = get_logger(__name__)


class WPAValidator:
    """Validador de contraseñas contra handshakes WPA/WPA2"""

    def __init__(self, handshake_file, essid, bssid):
        """
        Inicializa el validador
        
        Args:
            handshake_file: Ruta del archivo PCAP con handshake
            essid: Nombre de la red WiFi
            bssid: Dirección MAC de la red
        """
        self.handshake_file = handshake_file
        self.essid = essid
        self.bssid = bssid
        self.wordlist_file = None

    def validate_password(self, password):
        """
        Valida una contraseña contra el handshake
        
        Args:
            password: Contraseña a validar
            
        Returns:
            bool: True si la contraseña es correcta
        """
        try:
            # Crear wordlist temporal con la contraseña
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(password)
                temp_wordlist = f.name

            result = self._aircrack_validate(temp_wordlist)

            # Limpiar
            os.unlink(temp_wordlist)

            return result

        except Exception as e:
            logger.debug(f"Error validando contraseña: {e}")
            return False

    def _aircrack_validate(self, wordlist_file):
        """
        Valida usando aircrack-ng
        
        Args:
            wordlist_file: Archivo con contraseñas a validar
            
        Returns:
            bool: True si la contraseña fue correcta
        """
        try:
            cmd = [
                config.AIRCRACK_NG_PATH,
                self.handshake_file,
                '-w', wordlist_file,
                '-q',  # Quiet mode
                '-b', self.bssid
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.TIMEOUT_PER_ATTEMPT
            )

            # aircrack-ng muestra "KEY FOUND" cuando descubre la contraseña
            if "KEY FOUND" in result.stdout or "key found" in result.stdout.lower():
                # Extraer la contraseña encontrada
                for line in result.stdout.split('\n'):
                    if "KEY" in line or "key" in line:
                        logger.info(f"¡Contraseña encontrada! {line}")
                        return True

            return False

        except subprocess.TimeoutExpired:
            logger.debug("Timeout en aircrack-ng")
            return False
        except Exception as e:
            logger.debug(f"Error en aircrack-ng: {e}")
            return False

    def batch_validate(self, passwords):
        """
        Valida múltiples contraseñas de una vez (más rápido)
        
        Args:
            passwords: Lista de contraseñas o generador
            
        Returns:
            tuple: (contraseña_correcta, num_intentos)
        """
        try:
            # Crear wordlist temporal
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                count = 0
                for password in passwords:
                    f.write(password + '\n')
                    count += 1

                temp_wordlist = f.name

            # Validar con aircrack-ng
            cmd = [
                config.AIRCRACK_NG_PATH,
                self.handshake_file,
                '-w', temp_wordlist,
                '-b', self.bssid
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.TIMEOUT_PER_ATTEMPT * count  # Escalar timeout
            )

            os.unlink(temp_wordlist)

            # Buscar la contraseña encontrada
            if "KEY FOUND" in result.stdout:
                # Extraer contraseña de la salida
                for line in result.stdout.split('\n'):
                    if "KEY" in line:
                        # Formato típico: "Key found! [ CONTRASEÑA ]"
                        match = line.split('[')
                        if len(match) > 1:
                            password = match[-1].split(']')[0].strip()
                            logger.info(f"¡Contraseña encontrada! {password}")
                            return password, count

            return None, count

        except Exception as e:
            logger.error(f"Error en validación batch: {e}")
            return None, 0

    @staticmethod
    def compute_pmk(password, ssid):
        """
        Computa el PMK (Pairwise Master Key) usando PBKDF2-HMAC-SHA1
        Este es el proceso interno de WPA
        
        Args:
            password: Contraseña WiFi
            ssid: SSID de la red
            
        Returns:
            bytes: PMK (32 bytes)
        """
        # WPA usa PBKDF2 con 4096 iteraciones
        pmk = hashlib.pbkdf2_hmac(
            'sha1',
            password.encode('utf-8'),
            ssid.encode('utf-8'),
            config.WPA_ITERATIONS
        )
        return pmk

    @staticmethod
    def compute_ptk(pmk, ap_mac, client_mac, anonce, snonce):
        """
        Computa el PTK (Pairwise Transient Key) a partir del PMK
        
        Args:
            pmk: Pairwise Master Key
            ap_mac: Dirección MAC del AP
            client_mac: Dirección MAC del cliente
            anonce: Nonce del AP
            snonce: Nonce del cliente
            
        Returns:
            bytes: PTK
        """
        # Concatenar en orden correcto (menor MAC primero)
        if ap_mac < client_mac:
            mac_data = ap_mac + client_mac
        else:
            mac_data = client_mac + ap_mac

        if anonce < snonce:
            nonce_data = anonce + snonce
        else:
            nonce_data = snonce + anonce

        # PRF-512 (Pseudo Random Function)
        data = b"Pairwise key expansion" + mac_data + nonce_data

        # HMAC-SHA1 iterado
        ptk = b""
        for i in range(5):
            ptk += hmac.new(pmk, data + bytes([i]), hashlib.sha1).digest()

        return ptk[:48]  # PTK es 384 bits (48 bytes)
