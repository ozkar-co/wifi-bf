#!/usr/bin/env python3
"""
WiFi-BF: Brute Force Testing Tool para Redes Inalámbricas
Script principal que coordina los ataques
"""
import argparse
import sys
import signal
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from utils.logger import get_logger
from utils.reporter import AttackReport
from methods.brute_force import BruteForcAttack

logger = get_logger(__name__)


class WiFiBruteForcer:
    """Coordinador principal de ataques de fuerza bruta"""

    def __init__(self, method="brute-force", threads=None, resume=False, **kwargs):
        """
        Inicializa el bruteforcer
        
        Args:
            method: Método de ataque a usar
            threads: Número de hilos (default: config.MAX_THREADS)
            resume: Si reanudar desde checkpoint
            **kwargs: Argumentos específicos del método
        """
        self.method_name = method
        self.threads = threads or config.MAX_THREADS
        self.resume = resume
        self.kwargs = kwargs
        self.attack_method = None
        self.report = None
        self.interrupted = False

        # Configurar manejador de Ctrl+C
        signal.signal(signal.SIGINT, self._handle_interrupt)

        logger.info(f"WiFi-BF inicializado - Método: {method}, Hilos: {self.threads}")

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
