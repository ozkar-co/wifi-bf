# WiFi-BF: Brute Force Testing Tool

Una herramienta educativa en Python para testear la seguridad de redes inalámbricas mediante diferentes métodos de ataque controlado. Esta aplicación implementa múltiples estrategias de cracking con recuperación automática ante fallos y generación de reportes detallados.

---

## DISCLAIMER IMPORTANTE

**ESTA HERRAMIENTA SOLO DEBE USARSE EN REDES PROPIAS O CON AUTORIZACIÓN EXPLÍCITA DEL PROPIETARIO.**

El acceso no autorizado a sistemas informáticos es ilegal en la mayoría de jurisdicciones. WiFi-BF es una herramienta desarrollada **exclusivamente con fines educativos** para:
- Aprender sobre seguridad de redes
- Testear la robustez de tus propias infraestructuras
- Investigación académica en ciberseguridad

El autor no es responsable del uso indebido de esta herramienta.

---

## Características Principales

### Métodos de Ataque

- **Fuerza Bruta Numérica**: Genera automáticamente combinaciones numéricas (0-9) en orden creciente
- **Ataque por Diccionario**: Utiliza listas de palabras comunes para acelerar el cracking
- **Métodos Heurísticos**: Variaciones inteligentes de palabras, números y símbolos basadas en patrones comunes

### Recuperación y Persistencia

- **Checkpoints Automáticos**: Guarda el progreso cada 1000 intentos (configurable)
- **Recuperación ante Fallos**: Reanuda automáticamente desde el último checkpoint en caso de interrupción
- **Logging Detallado**: Registro completo de intentos, errores y puntos de control

### Reportes y Estadísticas

Al romper una contraseña, genera un reporte completo que incluye:

- **Tiempo total de ejecución**
- **Hilos utilizados**
- **Memoria RAM consumida**
- **Método que funcionó** (Fuerza Bruta / Diccionario / Heurístico)
- **Número de intentos realizados**
- **Velocidad promedio (intentos/segundo)**
- **Contraseña encontrada** (opcionalmente enmascarada)
- **Timestamp de finalización**

---

## Requisitos

- Python 3.8 o superior
- Librerías estándar de Python
- Permiso de administrador

---

## Instalación

```bash
# Clonar o descargar el repositorio
git clone https://github.com/ozkar-co/wifi-bf.git
cd wifi-bf

# (Opcional) Crear un entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias (si las hay)
pip install -r requirements.txt
```

---

## Uso

### Ataque por Fuerza Bruta Numérica

```bash
python wifi_bf.py --method brute-force --min-length 4 --max-length 8 --threads 4
```

### Ataque por Diccionario

```bash
python wifi_bf.py --method dictionary --wordlist diccionario.txt --threads 4
```

### Ataque Heurístico

```bash
python wifi_bf.py --method heuristic --threads 4 --variations
```

### Con Recuperación desde Checkpoint

```bash
python wifi_bf.py --method dictionary --wordlist diccionario.txt --resume
```

---

## Estructura de Archivos

```
wifi-bf/
├── README.md                  # Este archivo
├── requirements.txt           # Dependencias del proyecto
├── wifi_bf.py                # Script principal
├── config.py                 # Configuración general
├── methods/
│   ├── brute_force.py       # Módulo de fuerza bruta
│   ├── dictionary.py        # Módulo de diccionario
│   └── heuristic.py         # Módulo heurístico
├── utils/
│   ├── checkpoint.py        # Sistema de checkpoints
│   ├── logger.py            # Sistema de logging
│   └── reporter.py          # Generación de reportes
├── logs/                     # Directorio de logs y checkpoints
│   └── checkpoints/         # Puntos de recuperación
├── wordlists/               # Diccionarios de ejemplo
│   └── common_passwords.txt
└── examples/                # Scripts de ejemplo
    └── example_usage.py
```

---

## Sistema de Checkpoints

El sistema de checkpoints guarda automáticamente el progreso en intervalos regulares:

- **Diccionario**: Cada 1000 palabras procesadas
- **Fuerza Bruta**: Cada 1000 intentos
- **Heurístico**: Cada 1000 variaciones generadas

**Ubicación**: `logs/checkpoints/checkpoint_[método]_[timestamp].json`

Los checkpoints contienen:
- Último intento realizado
- Línea/índice actual
- Intentos totales
- Tiempo transcurrido
- Estado de recursos

---

## Ejemplo de Reporte

```
╔════════════════════════════════════════════════════════════════╗
║                    REPORTE DE CRACKING                         ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  RESULTADO: ¡CONTRASEÑA ENCONTRADA!                            ║
║                                                                ║
║  Contraseña: 1234567890                                        ║
║  Método: Diccionario                                           ║
║                                                                ║
║  Tiempo Total: 2 min 43 seg                                    ║
║  Intentos Realizados: 15,847                                   ║
║  Velocidad: 97.5 intentos/segundo                              ║
║                                                                ║
║  Hilos Utilizados: 4                                           ║
║  Pico de Memoria: 256 MB                                       ║
║  CPU Promedio: 78.5%                                           ║
║                                                                ║
║  Finalización: 2026-02-27 14:32:15                             ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Configuración Avanzada

Edita `config.py` para ajustar:

```python
# Número máximo de hilos
MAX_THREADS = 4

# Intervalo de checkpoint (en intentos)
CHECKPOINT_INTERVAL = 1000

# Directorio de logs
LOG_DIR = "logs/"

# Mostrar intentos en tiempo real
VERBOSE = True

# Timeout por intento (segundos)
TIMEOUT_PER_ATTEMPT = 30
```

---

## Logging

Todos los eventos se registran en `logs/wifi_bf.log`:

- Inicio y fin de sesiones
- Cada checkpoint guardado
- Errores y excepciones
- Intentos exitosos
- Información de recursos

---

## Troubleshooting

**Q: El programa se congela**
- Reduce el número de hilos con `--threads 2`
- Verifica que el diccionario sea válido

**Q: ¿Cómo reanudo desde un checkpoint?**
- Usa `--resume` para continuar automáticamente
- El programa detectará el checkpoint más reciente

**Q: ¿Puedo usar mi propio diccionario?**
- Sí, con `--wordlist /ruta/a/tu/diccionario.txt`

**Q: ¿Qué significan los diferentes métodos?**
- **Brute Force**: Prueba todas las combinaciones posibles (lento pero exhaustivo)
- **Dictionary**: Prueba palabras de una lista (rápido pero limitado)
- **Heuristic**: Variaciones inteligentes (equilibrio entre velocidad y cobertura)

---

## Recursos Educativos

- [OWASP: Testing Wireless Security](https://owasp.org/)
- [RFC 2898: PBKDF2](https://tools.ietf.org/html/rfc2898)
- [WiFi WPA/WPA2 Security](https://www.wi-fi.org/)

---

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/MiFeature`)
3. Commit tus cambios (`git commit -m 'Añade MiFeature'`)
4. Push a la rama (`git push origin feature/MiFeature`)
5. Abre un Pull Request

**Áreas de mejora sugeridas:**
- Optimizaciones de rendimiento
- Nuevos métodos de ataque (rainbow tables, GPU)
- Mejoras en interfaz de usuario
- Soporte para diferentes estándares de encriptación

---

## Licencia

Este proyecto se distribuye bajo la licencia MIT (ver archivo `LICENSE`).

**Recordatorio**: El uso indebido de esta herramienta es responsabilidad del usuario y puede ser sancionado legalmente.

---

## Autor

Desarrollado por Ozkar-co como herramienta educativa para aprendizaje en ciberseguridad.

---

## Casos de Uso Legítimos

- Análisis de seguridad en tus propias redes
- Testing de calidad de contraseñas
- Laboratorios educativos de ciberseguridad
- Investigación académica en seguridad inalámbrica
- Red teaming autorizado

---

**Última actualización**: Febrero 2026

