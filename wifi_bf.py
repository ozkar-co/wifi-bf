#!/usr/bin/env python3
"""
WiFi-BF: Brute Force Testing Tool para Redes WiFi Reales
Ataca redes WPA/WPA2 capturando handshakes y validando contraseñas
SOLO PARA REDES PROPIAS O CON AUTORIZACIÓN EXPLÍCITA
"""
import argparse
import sys
import signal
import time
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from utils.logger import get_logger
from utils.reporter import AttackReport
from utils.wifi_capture import WiFiCapture
from utils.wpa_validator import WPAValidator
from methods.brute_force import BruteForcAttack

logger = get_logger(__name__)


class WiFiBruteForcer:
    """Coordinador principal de ataques de fuerza bruta WiFi"""

    def __init__(self, interface=None, method="brute-force", threads=None, resume=False, **kwargs):
        """
        Inicializa el bruteforcer
        
        Args:
            interface: Interfaz WiFi a usar
            method: Método de ataque
            threads: Número de hilos
            resume: Si reanudar desde checkpoint
            **kwargs: Argumentos específicos del método
        """
        self.interface = interface
        self.method_name = method
        self.threads = threads or config.MAX_THREADS
        self.resume = resume
        self.kwargs = kwargs
        self.attack_method = None
        self.report = None
        self.interrupted = False
        self.wifi_capture = WiFiCapture(interface)

        # Configurar manejador de Ctrl+C
        signal.signal(signal.SIGINT, self._handle_interrupt)

        logger.info(f"WiFi-BF inicializado - Interfaz: {interface}, Método: {method}")

    def _handle_interrupt(self, signum, frame):
        """Maneja la interrupción por Ctrl+C"""
        logger.warning("Interrupción detectada. Finalizando...")
        self.interrupted = True
        self.wifi_capture.cleanup()

    def list_networks(self, timeout=15):
        """
        Lista redes WiFi disponibles
        
        Args:
            timeout: Segundos para escanear
        """
        logger.info("Listando redes disponibles...")
        
        try:
            networks = self.wifi_capture.scan_networks(timeout)
            
            if not networks:
                logger.info("No se encontraron redes")
                return
            
            print("\n" + "="*80)
            print("REDES ENCONTRADAS".center(80))
            print("="*80)
            print(f"{'Num':<5} {'ESSID':<30} {'BSSID':<20} {'Power':<10} {'Encrypt':<10}")
            print("-"*80)
            
            for i, net in enumerate(networks, 1):
                if net['Power'] >= config.MIN_SIGNAL_STRENGTH:
                    print(
                        f"{i:<5} {net['ESSID']:<30} {net['BSSID']:<20} "
                        f"{net['Power']:<10} {net['Encryption']:<10}"
                    )
            
            print("="*80 + "\n")
            return networks

        except KeyboardInterrupt:
            logger.info("Escaneo cancelado")
        except Exception as e:
            logger.error(f"Error listando redes: {e}")
            return None

    def capture_and_attack(self, essid, bssid):
        """
        Captura el handshake de una red y la ataca
        
        Args:
            essid: Nombre de la red
            bssid: Dirección MAC de la red
        """
        logger.info(f"Iniciando captura para {essid} ({bssid})")
        
        try:
            # Capturar handshake
            handshake_file = self.wifi_capture.capture_handshake(essid, bssid)
            
            if not handshake_file:
                logger.error("No se pudo capturar el handshake")
                return None
            
            logger.info(f"Handshake capturado: {handshake_file}")
            
            # Crear validador
            validator = WPAValidator(handshake_file, essid, bssid)
            
            # Ejecutar ataque
            return self._execute_attack(essid, validator)

        except KeyboardInterrupt:
            logger.info("Ataque cancelado")
            return None
        except Exception as e:
            logger.error(f"Error en ataque: {e}")
            return None

    def _execute_attack(self, essid, validator):
        """
        Ejecuta el ataque contra un validador
        
        Args:
            essid: Nombre de la red (para reporte)
            validator: Objeto validador WPA
            
        Returns:
            AttackReport: Reporte del ataque
        """
        # Configurar método
        self.setup_attack_method(validator)
        self.attack_method.start()

        # Crear reporte
        self.report = AttackReport(self.method_name, datetime.now())
        self.report.stats['target'] = essid

        try:
            self._process_candidates(validator)

            if self.attack_method.success:
                self.report.set_success(
                    self.attack_method.result_password,
                    self.attack_method.attempts,
                    self.attack_method.get_memory_stats(),
                    self.attack_method.get_cpu_stats()
                )
                logger.info("Ataque exitoso!")
            elif self.interrupted:
                self.report.set_failure(
                    self.attack_method.attempts,
                    self.attack_method.get_memory_stats(),
                    self.attack_method.get_cpu_stats(),
                    reason="Interrumpido por usuario"
                )
            else:
                self.report.set_failure(
                    self.attack_method.attempts,
                    self.attack_method.get_memory_stats(),
                    self.attack_method.get_cpu_stats(),
                    reason="Contraseña no encontrada"
                )

        except Exception as e:
            logger.error(f"Error durante el ataque: {e}", exc_info=True)
            self.report.set_failure(
                self.attack_method.attempts,
                self.attack_method.get_memory_stats(),
                self.attack_method.get_cpu_stats(),
                reason=f"Error: {str(e)}"
            )
        finally:
            self.attack_method.stop()

        return self.report

    def _process_candidates(self, validator):
        """
        Procesa candidatos con validador
        
        Args:
            validator: Objeto WPAValidator
        """
        attempt_count = 0
        last_update = time.time()

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {}
            candidate_generator = self.attack_method.generate()

            # Llenar la cola inicial de futures
            for _ in range(self.threads * 2):
                try:
                    candidate = next(candidate_generator)
                    future = executor.submit(validator.validate_password, candidate)
                    futures[future] = candidate
                except StopIteration:
                    break

            # Procesar futures
            while futures and not self.interrupted:
                for future in as_completed(futures):
                    candidate = futures.pop(future)
                    
                    try:
                        is_valid = future.result()
                        self.attack_method.record_attempt(candidate)
                        attempt_count += 1

                        if is_valid:
                            self.attack_method.on_success(candidate)
                            for pending_future in futures:
                                pending_future.cancel()
                            return

                        try:
                            next_candidate = next(candidate_generator)
                            new_future = executor.submit(
                                validator.validate_password, 
                                next_candidate
                            )
                            futures[new_future] = next_candidate
                        except StopIteration:
                            pass

                        current_time = time.time()
                        if current_time - last_update >= 5:
                            self._print_progress(attempt_count)
                            last_update = current_time

                    except Exception as e:
                        logger.error(f"Error procesando {candidate}: {e}")

    def setup_attack_method(self, validator):
        """Configura el método de ataque"""
        if self.method_name == "brute-force":
            self.attack_method = BruteForcAttack(
                validator=validator,
                min_length=self.kwargs.get('min_length'),
                max_length=self.kwargs.get('max_length'),
                charset=self.kwargs.get('charset')
            )
        else:
            raise ValueError(f"Método desconocido: {self.method_name}")

    def _print_progress(self, attempts):
        """Imprime barra de progreso"""
        if hasattr(self.attack_method, 'get_progress_percentage'):
            progress = self.attack_method.get_progress_percentage()
            duration = self.attack_method.get_duration()
            per_second = attempts / duration if duration > 0 else 0

            print(
                f"\r Intentos: {attempts:,} | Velocidad: {per_second:.1f} intentos/seg",
                end='',
                flush=True
            )


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='WiFi-BF: Ataque a redes WiFi WPA/WPA2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EJEMPLOS DE USO:

  # Listar redes disponibles
  sudo python3 wifi_bf.py -i wlan0 --scan

  # Atacar una red específica
  sudo python3 wifi_bf.py -i wlan0 --attack "Mi Red" "AA:BB:CC:DD:EE:FF"

  # Análisis detallado
  sudo python3 wifi_bf.py -i wlan0 --scan --verbose

REQUISITOS:
  - Ejecutar como root (sudo)
  - aircrack-ng instalado
  - Interfaz WiFi con soporte monitor mode

DISCLAIMER:
  Solo usar en redes propias o con autorización explícita.
  El acceso no autorizado es ilegal.
        """
    )

    parser.add_argument(
        '-i', '--interface',
        required=False,
        help='Interfaz WiFi a usar (ej: wlan0)'
    )

    parser.add_argument(
        '--scan',
        action='store_true',
        help='Escanear redes disponibles'
    )

    parser.add_argument(
        '--attack',
        nargs=2,
        metavar=('ESSID', 'BSSID'),
        help='Atacar network específica'
    )

    parser.add_argument(
        '--method',
        default='brute-force',
        choices=['brute-force', 'dictionary'],
        help='Método de ataque'
    )

    parser.add_argument(
        '--threads',
        type=int,
        default=config.MAX_THREADS,
        help=f'Número de hilos (default: {config.MAX_THREADS})'
    )

    parser.add_argument(
        '--min-length',
        type=int,
        default=config.BRUTE_FORCE_MIN_LENGTH,
        help=f'Longitud mínima (default: {config.BRUTE_FORCE_MIN_LENGTH})'
    )

    parser.add_argument(
        '--max-length',
        type=int,
        default=config.BRUTE_FORCE_MAX_LENGTH,
        help=f'Longitud máxima (default: {config.BRUTE_FORCE_MAX_LENGTH})'
    )

    parser.add_argument(
        '--charset',
        default=config.BRUTE_FORCE_START_CHARSET,
        help='Caracteres a probar'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Modo verbose'
    )

    args = parser.parse_args()

    # Verificar que se especifique interfaz
    if not args.interface:
        parser.error("Debes especificar interfaz con -i/--interface")

    # Crear instancia
    bruteforcer = WiFiBruteForcer(
        interface=args.interface,
        method=args.method,
        threads=args.threads,
        min_length=args.min_length,
        max_length=args.max_length,
        charset=args.charset
    )

    try:
        # Verificar permisos y herramientas
        bruteforcer.wifi_capture.check_root_privileges()
        bruteforcer.wifi_capture.check_aircrack_ng()

        if args.scan:
            # Escanear redes
            bruteforcer.list_networks()

        elif args.attack:
            # Atacar red específica
            essid, bssid = args.attack
            report = bruteforcer.capture_and_attack(essid, bssid)
            
            if report:
                report.save()
                report.print_summary()
                return 0 if report.stats['password_found'] else 1

        else:
            # Sin opciones válidas
            parser.print_help()
            return 1

        return 0

    except PermissionError as e:
        logger.error(f"Permiso denegado: {e}")
        return 1
    except FileNotFoundError as e:
        logger.error(f"Herramienta faltante: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Operación cancelada")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())


    def _handle_interrupt(self, signum, frame):
        """Maneja la interrupción por Ctrl+C"""
        logger.warning("Interrupción detectada. Finalizando...")
        self.interrupted = True

    def setup_attack_method(self):
        """Configura el método de ataque según los parámetros"""
        if self.method_name == "brute-force":
            self.attack_method = BruteForcAttack(
                min_length=self.kwargs.get('min_length'),
                max_length=self.kwargs.get('max_length'),
                charset=self.kwargs.get('charset')
            )
        else:
            logger.error(f"Método desconocido: {self.method_name}")
            raise ValueError(f"Método desconocido: {self.method_name}")

    def start_attack(self, target_password):
        """
        Inicia el ataque
        
        Args:
            target_password: Contraseña a romper
            
        Returns:
            AttackReport: Reporte del ataque
        """
        logger.info(f"Iniciando ataque - Contraseña objetivo: {self._mask_password(target_password)}")
        
        # Configurar método
        self.setup_attack_method()
        self.attack_method.start()

        # Crear reporte
        self.report = AttackReport(self.method_name, datetime.now())

        try:
            # Ejecutar ataque
            self._execute_attack(target_password)

            if self.attack_method.success:
                self.report.set_success(
                    self.attack_method.result_password,
                    self.attack_method.attempts,
                    self.attack_method.get_memory_stats(),
                    self.attack_method.get_cpu_stats()
                )
                logger.info("Ataque exitoso!")
            elif self.interrupted:
                self.report.set_failure(
                    self.attack_method.attempts,
                    self.attack_method.get_memory_stats(),
                    self.attack_method.get_cpu_stats(),
                    reason="Interrumpido por usuario"
                )
                logger.info("Ataque interrumpido por usuario")
            else:
                self.report.set_failure(
                    self.attack_method.attempts,
                    self.attack_method.get_memory_stats(),
                    self.attack_method.get_cpu_stats(),
                    reason="Contraseña no encontrada"
                )
                logger.info("Ataque completado sin encontrar contraseña")

        except Exception as e:
            logger.error(f"Error durante el ataque: {e}", exc_info=True)
            self.report.set_failure(
                self.attack_method.attempts,
                self.attack_method.get_memory_stats(),
                self.attack_method.get_cpu_stats(),
                reason=f"Error: {str(e)}"
            )
        finally:
            self.attack_method.stop()

        return self.report

    def _execute_attack(self, target_password):
        """Ejecuta el ataque con múltiples hilos"""
        attempt_count = 0
        last_update = time.time()

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            # Crear futures para el generador
            futures = {}
            candidate_generator = self.attack_method.generate()

            # Llenar la cola inicial de futures
            for _ in range(self.threads * 2):  # Buffer de tareas
                try:
                    candidate = next(candidate_generator)
                    future = executor.submit(self._check_password, candidate, target_password)
                    futures[future] = candidate
                except StopIteration:
                    break

            # Procesar futures a medida que se completan
            while futures and not self.interrupted:
                for future in as_completed(futures):
                    candidate = futures.pop(future)
                    
                    try:
                        result = future.result()
                        self.attack_method.record_attempt(candidate)
                        attempt_count += 1

                        if result:  # Contraseña encontrada
                            self.attack_method.on_success(candidate)
                            # Cancelar todas las tareas pendientes
                            for pending_future in futures:
                                pending_future.cancel()
                            return

                        # Intentar obtener siguiente candidato
                        try:
                            next_candidate = next(candidate_generator)
                            new_future = executor.submit(self._check_password, next_candidate, target_password)
                            futures[new_future] = next_candidate
                        except StopIteration:
                            pass

                        # Mostrar progreso
                        current_time = time.time()
                        if current_time - last_update >= 5:  # Cada 5 segundos
                            self._print_progress(attempt_count)
                            last_update = current_time

                    except Exception as e:
                        logger.error(f"Error procesando {candidate}: {e}")

            self._print_final_stats(attempt_count)

    @staticmethod
    def _check_password(candidate, target):
        """
        Comprueba si un candidato es la contraseña correcta
        
        Args:
            candidate: Candidato a probar
            target: Contraseña objetivo
            
        Returns:
            bool: True si es correcto, False en caso contrario
        """
        return candidate == target

    def _print_progress(self, attempts):
        """Imprime barra de progreso y estadísticas"""
        if hasattr(self.attack_method, 'get_progress_percentage'):
            progress = self.attack_method.get_progress_percentage()
            duration = self.attack_method.get_duration()
            per_second = attempts / duration if duration > 0 else 0

            print(
                f"\r Intentos: {attempts:,} | Progreso: {progress:.2f}% | "
                f"Velocidad: {per_second:.1f} intentos/seg",
                end='',
                flush=True
            )

    def _print_final_stats(self, attempts):
        """Imprime estadísticas finales básicas"""
        print()  # Nueva línea después de la barra de progreso
        logger.info(f"Estadísticas finales - Intentos totales: {attempts:,}")

    @staticmethod
    def _mask_password(password, show_chars=2):
        """Enmascara la contraseña para logs"""
        if len(password) <= show_chars:
            return '*' * len(password)
        return password[:show_chars] + '*' * (len(password) - show_chars)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='WiFi-BF: Brute Force Testing Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Fuerza bruta numérica (4-8 dígitos)
  python wifi_bf.py --method brute-force --min-length 4 --max-length 8 --target password123

  # Reanudar desde checkpoint
  python wifi_bf.py --method brute-force --resume --target password123

  # Usar más hilos
  python wifi_bf.py --method brute-force --threads 8 --target password123
        """
    )

    parser.add_argument(
        '--method',
        default='brute-force',
        choices=['brute-force', 'dictionary', 'heuristic'],
        help='Método de ataque a usar (default: brute-force)'
    )
    
    parser.add_argument(
        '--target',
        required=True,
        help='Contraseña objetivo a romper'
    )
    
    parser.add_argument(
        '--threads',
        type=int,
        default=config.MAX_THREADS,
        help=f'Número de hilos a usar (default: {config.MAX_THREADS})'
    )
    
    parser.add_argument(
        '--min-length',
        type=int,
        default=config.BRUTE_FORCE_MIN_LENGTH,
        help=f'Longitud mínima (solo brute-force) (default: {config.BRUTE_FORCE_MIN_LENGTH})'
    )
    
    parser.add_argument(
        '--max-length',
        type=int,
        default=config.BRUTE_FORCE_MAX_LENGTH,
        help=f'Longitud máxima (solo brute-force) (default: {config.BRUTE_FORCE_MAX_LENGTH})'
    )
    
    parser.add_argument(
        '--charset',
        default=config.BRUTE_FORCE_CHARSET,
        help=f'Conjunto de caracteres a usar (default: "{config.BRUTE_FORCE_CHARSET}")'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Reanudar desde el último checkpoint'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Modo verbose (más información)'
    )

    args = parser.parse_args()

    # Crear instancia del bruteforcer
    bruteforcer = WiFiBruteForcer(
        method=args.method,
        threads=args.threads,
        resume=args.resume,
        min_length=args.min_length,
        max_length=args.max_length,
        charset=args.charset
    )

    # Ejecutar ataque
    report = bruteforcer.start_attack(args.target)

    # Guardar y mostrar reporte
    if report:
        report.save()
        report.print_summary()
        return 0 if report.stats['password_found'] else 1

    return 1


if __name__ == '__main__':
    sys.exit(main())
