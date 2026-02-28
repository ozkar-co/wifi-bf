"""
Sistema de reportes para WiFi-BF
"""
import json
import os
from datetime import datetime
import config
from utils.logger import get_logger

logger = get_logger(__name__)


class AttackReport:
    """Genera reportes de ataques"""

    def __init__(self, method_name, start_time):
        """
        Inicializa un reporte
        
        Args:
            method_name: Nombre del método usado
            start_time: Timestamp de inicio
        """
        self.method_name = method_name
        self.start_time = start_time
        self.end_time = None
        self.stats = {
            'method': method_name,
            'password_found': False,
            'password': None,
            'attempts': 0,
            'start_time': start_time,
            'end_time': None,
            'duration_seconds': 0,
            'duration_formatted': '',
            'attempts_per_second': 0,
            'threads_used': config.MAX_THREADS,
            'peak_memory_mb': 0,
            'average_cpu_percent': 0,
            'system_info': {}
        }

    def set_success(self, password, attempts, memory_stats, cpu_stats):
        """
        Marca el reporte como exitoso
        
        Args:
            password: Contraseña encontrada
            attempts: Número de intentos
            memory_stats: Dict con estadísticas de memoria
            cpu_stats: Dict con estadísticas de CPU
        """
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()

        self.stats['password_found'] = True
        self.stats['password'] = self._mask_password(password) if not config.SHOW_DECRYPTED_PASSWORD else password
        self.stats['password_raw'] = password  # Guardar sin enmascarar para logs internos
        self.stats['attempts'] = attempts
        self.stats['end_time'] = self.end_time.isoformat()
        self.stats['duration_seconds'] = duration
        self.stats['duration_formatted'] = self._format_duration(duration)
        self.stats['attempts_per_second'] = round(attempts / duration, 2) if duration > 0 else 0
        self.stats['peak_memory_mb'] = memory_stats.get('peak_mb', 0)
        self.stats['average_cpu_percent'] = cpu_stats.get('average', 0)
        self.stats['system_info'] = {
            'memory': memory_stats,
            'cpu': cpu_stats
        }

    def set_failure(self, attempts, memory_stats, cpu_stats, reason="Interrumpido por usuario"):
        """
        Marca el reporte como fallido
        
        Args:
            attempts: Número de intentos realizados
            memory_stats: Dict con estadísticas de memoria
            cpu_stats: Dict con estadísticas de CPU
            reason: Motivo del fallo
        """
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()

        self.stats['password_found'] = False
        self.stats['failure_reason'] = reason
        self.stats['attempts'] = attempts
        self.stats['end_time'] = self.end_time.isoformat()
        self.stats['duration_seconds'] = duration
        self.stats['duration_formatted'] = self._format_duration(duration)
        self.stats['attempts_per_second'] = round(attempts / duration, 2) if duration > 0 else 0
        self.stats['peak_memory_mb'] = memory_stats.get('peak_mb', 0)
        self.stats['average_cpu_percent'] = cpu_stats.get('average', 0)

    @staticmethod
    def _mask_password(password, show_chars=2):
        """Enmascara la contraseña para seguridad"""
        if len(password) <= show_chars:
            return '*' * len(password)
        return password[:show_chars] + '*' * (len(password) - show_chars)

    @staticmethod
    def _format_duration(seconds):
        """Formatea duración en segundos a formato legible"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        
        return " ".join(parts)

    def save(self, format_type=None):
        """
        Guarda el reporte en disco
        
        Args:
            format_type: "text", "json", o None para usar config
            
        Returns:
            str: Ruta del archivo guardado
        """
        if format_type is None:
            format_type = config.REPORT_FORMAT

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "json" or format_type == "both":
            self._save_json(timestamp)
        
        if format_type == "text" or format_type == "both":
            return self._save_text(timestamp)
        
        return None

    def _save_json(self, timestamp):
        """Guarda reporte en JSON"""
        filename = f"report_{self.method_name}_{timestamp}.json"
        filepath = os.path.join(config.REPORT_DIR, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
            logger.info(f"Reporte JSON guardado: {filename}")
            return filepath
        except Exception as e:
            logger.error(f"Error al guardar reporte JSON: {e}")
            return None

    def _save_text(self, timestamp):
        """Guarda reporte en texto formateado"""
        filename = f"report_{self.method_name}_{timestamp}.txt"
        filepath = os.path.join(config.REPORT_DIR, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self._format_text())
            logger.info(f"Reporte TXT guardado: {filename}")
            return filepath
        except Exception as e:
            logger.error(f"Error al guardar reporte TXT: {e}")
            return None

    def _format_text(self):
        """Formatea el reporte en texto"""
        lines = []
        lines.append("=" * 70)
        lines.append("REPORTE DE CRACKING - WiFi-BF".center(70))
        lines.append("=" * 70)
        lines.append("")

        if self.stats['password_found']:
            lines.append("RESULTADO: CONTRASEÑA ENCONTRADA".ljust(35) + "✓")
            lines.append("")
            lines.append(f"Contraseña: {self.stats['password']}")
        else:
            lines.append("RESULTADO: NO SE ENCONTRÓ LA CONTRASEÑA".ljust(35) + "✗")
            lines.append(f"Razón: {self.stats.get('failure_reason', 'Desconocida')}")
            lines.append("")

        lines.append("-" * 70)
        lines.append("ESTADÍSTICAS".center(70))
        lines.append("-" * 70)
        
        lines.append(f"Método: {self.stats['method']}")
        lines.append(f"Intentos realizados: {self.stats['attempts']:,}")
        lines.append(f"Velocidad: {self.stats['attempts_per_second']} intentos/segundo")
        lines.append("")
        lines.append(f"Tiempo total: {self.stats['duration_formatted']}")
        lines.append(f"  • Inicio: {self.stats['start_time']}")
        lines.append(f"  • Fin: {self.stats['end_time']}")
        lines.append("")
        lines.append(f"Hilos utilizados: {self.stats['threads_used']}")
        lines.append(f"Pico de memoria: {self.stats['peak_memory_mb']:.2f} MB")
        lines.append(f"CPU promedio: {self.stats['average_cpu_percent']:.1f}%")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)

    def print_summary(self):
        """Imprime un resumen del reporte en consola"""
        print("\n" + "=" * 70)
        print("REPORTE DE CRACKING - WiFi-BF".center(70))
        print("=" * 70)
        
        if self.stats['password_found']:
            print(f"\n✓ CONTRASEÑA ENCONTRADA")
            print(f"  Contraseña: {self.stats['password']}")
        else:
            print(f"\n✗ NO SE ENCONTRÓ LA CONTRASEÑA")
            print(f"  Razón: {self.stats.get('failure_reason', 'Desconocida')}")
        
        print(f"\nMétodo: {self.stats['method']}")
        print(f"Intentos: {self.stats['attempts']:,}")
        print(f"Velocidad: {self.stats['attempts_per_second']} intentos/seg")
        print(f"Duración: {self.stats['duration_formatted']}")
        print(f"\nHilos: {self.stats['threads_used']}")
        print(f"Memoria pico: {self.stats['peak_memory_mb']:.2f} MB")
        print(f"CPU promedio: {self.stats['average_cpu_percent']:.1f}%")
        print("\n" + "=" * 70)
