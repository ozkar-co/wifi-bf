"""
Método de ataque por fuerza bruta numérica para WiFi-BF
Genera todas las combinaciones posibles de números en orden creciente
"""
import itertools
import config
from methods import AttackMethod
from utils.logger import get_logger
from utils.checkpoint import CheckpointManager

logger = get_logger(__name__)


class BruteForcAttack(AttackMethod):
    """Método de fuerza bruta puro - prueba todas las combinaciones numéricas"""

    def __init__(self, min_length=None, max_length=None, charset=None):
        """
        Inicializa el método de fuerza bruta
        
        Args:
            min_length: Longitud mínima (default: config.BRUTE_FORCE_MIN_LENGTH)
            max_length: Longitud máxima (default: config.BRUTE_FORCE_MAX_LENGTH)
            charset: Caracteres a usar (default: config.BRUTE_FORCE_CHARSET)
        """
        super().__init__("brute-force")
        
        self.min_length = min_length or config.BRUTE_FORCE_MIN_LENGTH
        self.max_length = max_length or config.BRUTE_FORCE_MAX_LENGTH
        self.charset = charset or config.BRUTE_FORCE_CHARSET
        
        self.checkpoint_manager = CheckpointManager("brute-force")
        self.last_checkpoint_attempt = 0
        self.resume_from_length = self.min_length
        self.resume_from_index = 0
        
        logger.info(
            f"Fuerza Bruta inicializado: {self.min_length}-{self.max_length} caracteres, "
            f"charset: {self.charset}"
        )

    def generate(self):
        """
        Generador de candidatos por fuerza bruta
        
        Yields:
            str: Candidato (combinación de números)
        """
        # Intentar cargar desde checkpoint
        resume_data = self.checkpoint_manager.load_latest()
        if resume_data:
            self.resume_from_length = resume_data.get('current_length', self.min_length)
            self.resume_from_index = resume_data.get('current_index', 0)
            self.attempts = resume_data.get('attempt_number', 0)
            logger.info(
                f"Reanudando desde: longitud={self.resume_from_length}, "
                f"index={self.resume_from_index}, intentos={self.attempts}"
            )

        # Iterar sobre cada longitud
        for length in range(self.resume_from_length, self.max_length + 1):
            logger.debug(f"Generando candidatos de longitud: {length}")
            
            # Crear todas las combinaciones de esta longitud
            candidates = itertools.product(self.charset, repeat=length)
            
            # Si reanudamos, saltar hasta el índice correcto
            skip_count = self.resume_from_index if length == self.resume_from_length else 0
            
            for index, combination in enumerate(candidates):
                if index < skip_count:
                    continue
                
                candidate = ''.join(combination)
                
                # Guardar checkpoint periódicamente
                if (self.attempts - self.last_checkpoint_attempt) >= config.CHECKPOINT_INTERVAL:
                    self._save_checkpoint(length, index)
                    self.last_checkpoint_attempt = self.attempts
                
                yield candidate
            
            # Reset para la siguiente longitud
            self.resume_from_index = 0

    def _save_checkpoint(self, current_length, current_index):
        """Guarda el progreso actual"""
        checkpoint_data = {
            'attempt_number': self.attempts,
            'current_length': current_length,
            'current_index': current_index,
            'charset': self.charset,
            'min_length': self.min_length,
            'max_length': self.max_length
        }
        self.checkpoint_manager.save(checkpoint_data)

    def on_success(self, password):
        """Llamado cuando se encuentra la contraseña"""
        super().on_success(password)
        # Eliminar checkpoint de éxito
        self.checkpoint_manager.delete_latest()

    def get_total_combinations(self):
        """
        Calcula el total de combinaciones posibles
        
        Returns:
            int: Número total de combinaciones
        """
        total = 0
        charset_size = len(self.charset)
        
        for length in range(self.min_length, self.max_length + 1):
            total += charset_size ** length
        
        return total

    def get_progress_percentage(self):
        """
        Calcula el porcentaje de progreso
        
        Returns:
            float: Porcentaje (0-100)
        """
        total = self.get_total_combinations()
        if total == 0:
            return 0
        return (self.attempts / total) * 100
