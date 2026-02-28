"""
Módulo de métodos de ataque para WiFi-BF
Proporciona clase base y decoradores para facilitar la extensión
"""
from abc import ABC, abstractmethod
from datetime import datetime
import psutil
import config
from utils.logger import get_logger

logger = get_logger(__name__)


class AttackMethod(ABC):
    """Clase base para todos los métodos de ataque"""

    def __init__(self, name):
        """
        Inicializa un método de ataque
        
        Args:
            name: Nombre del método
        """
        self.name = name
        self.attempts = 0
        self.start_time = None
        self.end_time = None
        self.success = False
        self.result_password = None
        self.process = psutil.Process()
        self.memory_stats = {'peak_mb': 0, 'values': []}
        self.cpu_stats = {'average': 0, 'values': []}

    @abstractmethod
    def generate(self):
        """
        Generador que produce candidatos a probar
        
        Yields:
            str: Candidato (contraseña potencial)
        """
        pass

    def start(self):
        """Marca el inicio del ataque"""
        self.start_time = datetime.now()
        logger.info(f"Iniciando ataque con método: {self.name}")

    def stop(self):
        """Marca el fin del ataque y calcula estadísticas"""
        self.end_time = datetime.now()
        self._calculate_stats()
        logger.info(f"Ataque completado. Intentos: {self.attempts}")

    def record_attempt(self, candidate):
        """
        Registra un intento
        
        Args:
            candidate: Candidato probado
        """
        self.attempts += 1
        self._update_memory_stats()
        self._update_cpu_stats()

    def on_success(self, password):
        """
        Llamado cuando se encuentra la contraseña
        
        Args:
            password: Contraseña encontrada
        """
        self.success = True
        self.result_password = password
        logger.info(f"Contraseña encontrada: {self._mask_password(password)}")

    def _update_memory_stats(self):
        """Actualiza estadísticas de memoria"""
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            self.memory_stats['values'].append(memory_mb)
            
            if memory_mb > self.memory_stats['peak_mb']:
                self.memory_stats['peak_mb'] = memory_mb
        except Exception as e:
            logger.debug(f"Error al obtener memoria: {e}")

    def _update_cpu_stats(self):
        """Actualiza estadísticas de CPU"""
        try:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            self.cpu_stats['values'].append(cpu_percent)
        except Exception as e:
            logger.debug(f"Error al obtener CPU: {e}")

    def _calculate_stats(self):
        """Calcula estadísticas finales"""
        if self.cpu_stats['values']:
            self.cpu_stats['average'] = sum(self.cpu_stats['values']) / len(self.cpu_stats['values'])

    def get_memory_stats(self):
        """Retorna estadísticas de memoria"""
        return self.memory_stats

    def get_cpu_stats(self):
        """Retorna estadísticas de CPU"""
        return self.cpu_stats

    def get_duration(self):
        """Retorna duración en segundos"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    @staticmethod
    def _mask_password(password, show_chars=2):
        """Enmascara la contraseña para logs"""
        if len(password) <= show_chars:
            return '*' * len(password)
        return password[:show_chars] + '*' * (len(password) - show_chars)


__all__ = ['AttackMethod']
