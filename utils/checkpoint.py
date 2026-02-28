"""
Sistema de checkpoints para recuperación ante fallos
"""
import json
import os
from datetime import datetime
import config
from utils.logger import get_logger

logger = get_logger(__name__)


class CheckpointManager:
    """Gestor de checkpoints para recuperación de progreso"""

    def __init__(self, method_name):
        """
        Inicializa el gestor de checkpoints
        
        Args:
            method_name: Nombre del método (para nombrar el archivo)
        """
        self.method_name = method_name
        self.checkpoint_dir = config.CHECKPOINT_DIR
        self.current_checkpoint = None

    def save(self, data):
        """
        Guarda un checkpoint
        
        Args:
            data (dict): Datos a guardar (debe incluir 'attempt_number')
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"checkpoint_{self.method_name}_{timestamp}.json"
        filepath = os.path.join(self.checkpoint_dir, filename)

        checkpoint_data = {
            'method': self.method_name,
            'timestamp': datetime.now().isoformat(),
            'attempt_number': data.get('attempt_number', 0),
            **data
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Checkpoint guardado: {filename}")
            self.current_checkpoint = filepath
        except Exception as e:
            logger.error(f"Error al guardar checkpoint: {e}")

    def load_latest(self):
        """
        Carga el checkpoint más reciente del método
        
        Returns:
            dict: Datos del checkpoint o None si no existe
        """
        try:
            checkpoints = [
                f for f in os.listdir(self.checkpoint_dir)
                if f.startswith(f"checkpoint_{self.method_name}_")
            ]
            
            if not checkpoints:
                logger.info(f"No se encontraron checkpoints para {self.method_name}")
                return None
            
            # Ordenar por timestamp y obtener el más reciente
            checkpoints.sort(reverse=True)
            latest_checkpoint = checkpoints[0]
            filepath = os.path.join(self.checkpoint_dir, latest_checkpoint)

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Checkpoint cargado: {latest_checkpoint}")
            return data

        except Exception as e:
            logger.error(f"Error al cargar checkpoint: {e}")
            return None

    def delete_latest(self):
        """Elimina el checkpoint más reciente después de completar"""
        if self.current_checkpoint and os.path.exists(self.current_checkpoint):
            try:
                os.remove(self.current_checkpoint)
                logger.debug(f"Checkpoint eliminado: {self.current_checkpoint}")
            except Exception as e:
                logger.error(f"Error al eliminar checkpoint: {e}")

    @staticmethod
    def cleanup_old_checkpoints(days=7):
        """
        Elimina checkpoints más antiguos que X días
        
        Args:
            days: Días de antigüedad para eliminar
        """
        from datetime import timedelta
        
        try:
            now = datetime.now()
            cutoff = now - timedelta(days=days)
            
            for filename in os.listdir(config.CHECKPOINT_DIR):
                if not filename.startswith("checkpoint_"):
                    continue
                
                filepath = os.path.join(config.CHECKPOINT_DIR, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff:
                    os.remove(filepath)
                    logger.debug(f"Checkpoint antiguo eliminado: {filename}")
        except Exception as e:
            logger.error(f"Error al limpiar checkpoints: {e}")
