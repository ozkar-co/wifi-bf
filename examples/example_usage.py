#!/usr/bin/env python3
"""
Ejemplo de uso de WiFi-BF
Demuestra cómo usar la herramienta con diferentes métodos
"""
import os
import sys

# Agregar el directorio padre al path para importar wifi_bf
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wifi_bf import WiFiBruteForcer
from utils.reporter import AttackReport
from datetime import datetime


def example_brute_force():
    """Ejemplo de ataque por fuerza bruta numérica"""
    print("\n" + "="*70)
    print("EJEMPLO: Fuerza Bruta Numérica".center(70))
    print("="*70 + "\n")

    # Crear instancia del bruteforcer
    bruteforcer = WiFiBruteForcer(
        method="brute-force",
        threads=4,
        min_length=4,
        max_length=6,
        charset="0123456789"
    )

    # Ejecutar ataque
    target_password = "12345"  # Contraseña objetivo
    print(f"Objetivo: {bruteforcer._mask_password(target_password)}")
    print(f"Rango: 4-6 dígitos")
    print(f"Caracteres: 0-9")
    print()

    report = bruteforcer.start_attack(target_password)

    # Mostrar resultados
    if report.stats['password_found']:
        print(f"\n✓ ¡Éxito! La contraseña fue encontrada")
        print(f"  Intentos: {report.stats['attempts']:,}")
        print(f"  Tiempo: {report.stats['duration_formatted']}")
        print(f"  Velocidad: {report.stats['attempts_per_second']} intentos/seg")
    else:
        print(f"\n✗ No se encontró la contraseña")


def example_with_resume():
    """Ejemplo mostrando cómo usar checkpoints"""
    print("\n" + "="*70)
    print("EJEMPLO: Con Checkpoints (Resume)".center(70))
    print("="*70 + "\n")

    print("Los checkpoints se guardan automáticamente cada 1000 intentos.")
    print("Si el programa se interrumpe, puede reanudarse con --resume\n")

    bruteforcer = WiFiBruteForcer(
        method="brute-force",
        threads=4,
        resume=False,  # Primera ejecución
        min_length=4,
        max_length=7,
        charset="0123456789"
    )

    target_password = "123456"
    report = bruteforcer.start_attack(target_password)
    report.print_summary()


def example_custom_charset():
    """Ejemplo con charset personalizado"""
    print("\n" + "="*70)
    print("EJEMPLO: Charset Personalizado".center(70))
    print("="*70 + "\n")

    # Atacar contraseña con números y letras
    bruteforcer = WiFiBruteForcer(
        method="brute-force",
        threads=2,
        min_length=3,
        max_length=4,
        charset="0123456789ab"  # Números y letras a-b
    )

    target_password = "a1b2"
    print(f"Objetivo: {bruteforcer._mask_password(target_password)}")
    print(f"Charset: 0123456789ab")
    print()

    report = bruteforcer.start_attack(target_password)
    report.print_summary()


if __name__ == '__main__':
    print("\n" + "█" * 70)
    print("WiFi-BF - Ejemplos de Uso".center(70))
    print("█" * 70)

    # Ejecutar ejemplos
    try:
        # Ejemplo 1: Fuerza bruta simple
        example_brute_force()

        # Ejemplo 2: Con checkpoints
        # example_with_resume()  # Descomenta para ejecutar

        # Ejemplo 3: Charset personalizado
        # example_custom_charset()  # Descomenta para ejecutar

    except KeyboardInterrupt:
        print("\n\nEjecución interrumpida por el usuario.")
    except Exception as e:
        print(f"\nError durante la ejecución: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "█" * 70)
    print("Fin de los ejemplos".center(70))
    print("█" * 70 + "\n")
