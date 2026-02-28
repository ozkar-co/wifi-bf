# WiFi-BF - Guía de Uso

Una guía completa para utilizar WiFi-BF en diferentes escenarios.

---

## Tabla de contenidos

1. [Instalación](#instalación)
2. [Uso básico](#uso-básico)
3. [Métodos de ataque](#métodos-de-ataque)
4. [Opciones CLI](#opciones-cli)
5. [Ejemplos prácticos](#ejemplos-prácticos)
6. [Checkpoints y recuperación](#checkpoints-y-recuperación)
7. [Interpretación de reportes](#interpretación-de-reportes)
8. [Troubleshooting](#troubleshooting)

---

## Instalación

### Requisitos previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/ozkar-co/wifi-bf.git
cd wifi-bf

# 2. (Opcional) Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

### Verificar instalación

```bash
python wifi_bf.py --help
```

Deberías ver la ayuda de la herramienta con todas las opciones disponibles.

---

## Uso básico

### Comando general

```bash
python wifi_bf.py --method METHOD --target PASSWORD [OPCIONES]
```

Parámetros obligatorios:
- `--method`: Método de ataque (brute-force, dictionary, heuristic)
- `--target`: Contraseña a romper

### Ejemplo más simple

```bash
python wifi_bf.py --method brute-force --target 12345
```

Este comando:
- Usa fuerza bruta numérica (por defecto 4-10 dígitos)
- Intenta encontrar la contraseña "12345"
- Utiliza 4 hilos (por defecto)

---

## Métodos de ataque

### 1. Fuerza Bruta Numérica (`brute-force`)

Genera automáticamente todas las combinaciones numéricas en orden creciente.

**Ventajas:**
- Garantizado encontrar la contraseña si es solo números
- Predecible y exhaustivo
- Fácil de resumir desde checkpoints

**Desventajas:**
- Lento para contraseñas largas
- No funciona con letras o símbolos

**Sintaxis:**
```bash
python wifi_bf.py --method brute-force --target PASSWORD \
    [--min-length NUM] [--max-length NUM] [--charset CHARS]
```

**Ejemplos:**

```bash
# Buscar PIN de 4-6 dígitos
python wifi_bf.py --method brute-force --target 54321 \
    --min-length 4 --max-length 6

# Buscar con charset personalizado (números + letras)
python wifi_bf.py --method brute-force --target a1b2c3 \
    --charset "0123456789abcdefghijklmnopqrstuvwxyz" \
    --min-length 6 --max-length 6

# Búsqueda lenta pero exhaustiva
python wifi_bf.py --method brute-force --target mypassword123 \
    --min-length 1 --max-length 15 \
    --charset "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%"
```

### 2. Diccionario (`dictionary`)

_Disponible próximamente_

Prueba palabras de una lista predefinida, más rápido pero limitado a palabras conocidas.

### 3. Heurístico (`heuristic`)

_Disponible próximamente_

Genera variaciones inteligentes de palabras comunes basadas en patrones.

---

## Opciones CLI

### Opciones globales

```
--method METHOD         Método de ataque (brute-force, dictionary, heuristic)
                       Default: brute-force

--target PASSWORD       Contraseña objetivo a romper
                       Obligatorio

--threads NUM          Número de hilos paralelos
                       Default: 4
                       Rango recomendado: 2-16
```

### Opciones de fuerza bruta

```
--min-length NUM       Longitud mínima de candidatos
                       Default: 4

--max-length NUM       Longitud máxima de candidatos
                       Default: 10

--charset CHARS        Caracteres a usar en generación
                       Default: "0123456789" (solo números)
                       
                       Ejemplos:
                       - "0123456789" (números)
                       - "abcdefghijklmnopqrstuvwxyz" (minúsculas)
                       - "0123456789abc" (números + algunas letras)
```

### Opciones de control

```
--resume               Reanudar desde el último checkpoint
                       útil después de una interrupción
                       Default: False

--verbose              Mostrar información detallada
                       Default: False
```

---

## Ejemplos prácticos

### Caso 1: Encontrar PIN simple

```bash
# Objetivo: Contraseña de 4 dígitos
python wifi_bf.py --method brute-force --target 7331 \
    --min-length 4 --max-length 4
```

**Salida esperada:**
```
Intentos: 7,332 | Progreso: 73.32% | Velocidad: 2450.5 intentos/seg
```

---

### Caso 2: Búsqueda con múltiples hilos (más rápido)

```bash
# Usar 8 hilos en lugar de 4
python wifi_bf.py --method brute-force --target password123 \
    --min-length 8 --max-length 8 \
    --charset "0123456789abcdefghijklmnopqrstuvwxyz" \
    --threads 8
```

**Ventajas:**
- Más rápido (distribución de carga)
- Mayor uso de CPU y memoria
- Ideal para máquinas multihilo

---

### Caso 3: Búsqueda exhaustiva con reanudación

```bash
# Primera ejecución (interrúmpela con Ctrl+C después de un tiempo)
python wifi_bf.py --method brute-force --target mysecret \
    --min-length 1 --max-length 12 \
    --charset "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Ctrl+C después de unos minutos...

# Reanudar desde donde se pausó
python wifi_bf.py --method brute-force --resume --target mysecret
```

**Nota:** El programa recordará exactamente dónde estaba y continuará desde ahí.

---

### Caso 4: Testing de contraseña débil

```bash
# Verificar si una contraseña se puede romper rápidamente
python wifi_bf.py --method brute-force --target abc123 \
    --min-length 6 --max-length 6 \
    --charset "0123456789abcdefghijklmnopqrstuvwxyz" \
    --threads 6
```

Si se rompe rápidamente, la contraseña es débil.

---

### Caso 5: Charset personalizado

```bash
# Solo números y letras minúsculas (sin símbolos)
python wifi_bf.py --method brute-force --target test1234 \
    --charset "0123456789abcdefghijklmnopqrstuvwxyz"

# Incluir mayúsculas también
python wifi_bf.py --method brute-force --target Test1234 \
    --charset "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Con símbolos comunes
python wifi_bf.py --method brute-force --target Pass@1234 \
    --charset "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()"
```

---

## Checkpoints y Recuperación

### Cómo funcionan los checkpoints

WiFi-BF guarda el progreso automáticamente cada 1000 intentos:

1. **Ubicación:** `logs/checkpoints/checkpoint_brute-force_[timestamp].json`
2. **Contenido:** Intento actual, longitud, índice, estadísticas
3. **Automático:** Se crea sin intervención del usuario
4. **Limpieza:** Se elimina automaticamente al completar el ataque

### Usar checkpoints para reanudar

```bash
# Si el programa se interrumpe (Ctrl+C o error)
# Se guarda un checkpoint automáticamente

# Para reanudar:
python wifi_bf.py --method brute-force --resume --target PASSWORD
```

El programa detectará automáticamente:
- El método (brute-force)
- El último punto de progreso
- Los parámetros originales

### Ver checkpoints disponibles

```bash
# Listar todos los checkpoints guardados
ls logs/checkpoints/
```

Ejemplo de contenido de checkpoint:
```json
{
  "method": "brute-force",
  "timestamp": "2026-02-27T14:32:15.123456",
  "attempt_number": 15847,
  "current_length": 5,
  "current_index": 847,
  "charset": "0123456789",
  "min_length": 4,
  "max_length": 10
}
```

---

## Interpretación de reportes

### Recepción de reporte

Cuando termina un ataque, WiFi-BF genera un reporte:

```
======================================================================
REPORTE DE CRACKING - WiFi-BF
======================================================================

RESULTADO: CONTRASEÑA ENCONTRADA
  Contraseña: 12***

Método: brute-force
Intentos: 15,847
Velocidad: 97.5 intentos/seg
Duración: 2 min 43 seg

Hilos: 4
Memoria pico: 256 MB
CPU promedio: 78.5%

======================================================================
```

### Campos del reporte

| Campo | Explicación |
|-------|------------|
| Resultado | Encontrada o no encontrada |
| Contraseña | Parcialmente enmascarada por seguridad |
| Método | Qué estrategia se utilizó |
| Intentos | Cuántos candidatos se probaron |
| Velocidad | Intentos por segundo (mayor=mejor) |
| Duración | Tiempo total del ataque |
| Hilos | Paralelismo utilizado |
| Memoria pico | RAM máxima consumida |
| CPU promedio | Uso de procesador promedio |

### Archivos de reporte

Los reportes se guardan en dos formatos:

**Texto:**
```
logs/reports/report_brute-force_20260227_143215.txt
```

**JSON (para análisis programático):**
```
logs/reports/report_brute-force_20260227_143215.json
```

---

## Troubleshooting

### Problema: "Python no encontrado"

**Síntoma:**
```
Python was not found; run without arguments to install from the Microsoft Store
```

**Soluciones:**
```bash
# Opción 1: Usar py launcher (Windows)
py wifi_bf.py --method brute-force --target 12345

# Opción 2: Usar python3
python3 wifi_bf.py --method brute-force --target 12345

# Opción 3: Especificar ruta completa a Python
C:\Python39\python.exe wifi_bf.py --method brute-force --target 12345
```

---

### Problema: "ModuleNotFoundError: No module named 'psutil'"

**Síntoma:**
```
ModuleNotFoundError: No module named 'psutil'
```

**Solución:**
```bash
# Instalar dependencias
pip install -r requirements.txt

# O instalar específicamente
pip install psutil colorama
```

---

### Problema: El programa es muy lento

**Síntomas:**
- Menos de 100 intentos/segundo
- CPU no está siendo utilizado completamente

**Soluciones:**

```bash
# Aumentar hilos
python wifi_bf.py --method brute-force --target PASSWORD \
    --threads 8  # Aumentar de 4 a 8

# Reducir rango de búsqueda
python wifi_bf.py --method brute-force --target PASSWORD \
    --min-length 5 --max-length 8  # En lugar de 4-10

# Reducir charset
python wifi_bf.py --method brute-force --target PASSWORD \
    --charset "0123456789"  # Solo números, más rápido
```

---

### Problema: "Permission denied" (Linux/Mac)

**Síntoma:**
```
bash: wifi_bf.py: Permission denied
```

**Solución:**
```bash
# Hacer el archivo ejecutable
chmod +x wifi_bf.py

# Luego ejecutar directamente
./wifi_bf.py --method brute-force --target 12345

# O ejecutar con python
python wifi_bf.py --method brute-force --target 12345
```

---

### Problema: La contraseña no se encuentra (pero debería)

**Verificar:**

1. **¿El charset incluye los caracteres de la contraseña?**
   ```bash
   # Contraseña: "Test1$"
   # Este charset NO la encontraría
   python wifi_bf.py --method brute-force --target "Test1$" \
       --charset "0123456789abc"  # Falta: T, mayúsculas, $
   
   # Este SÍ la encontraría
   python wifi_bf.py --method brute-force --target "Test1$" \
       --charset "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()"
   ```

2. **¿Las longitudes mín/máx incluyen la longitud real?**
   ```bash
   # Contraseña: "test" (4 caracteres)
   # Este NO la encontraría
   python wifi_bf.py --method brute-force --target "test" \
       --min-length 5 --max-length 10  # Empieza en 5, "test" tiene 4
   
   # Este SÍ la encontraría
   python wifi_bf.py --method brute-force --target "test" \
       --min-length 4 --max-length 10
   ```

3. **¿Estás buscando una contraseña exacta?**
   ```bash
   # Verifica que no haya espacios o caracteres invisibles
   target="test123"  # Sin espacios antes o después
   python wifi_bf.py --method brute-force --target "$target"
   ```

---

### Problema: Uso excesivo de memoria

**Síntomas:**
- La máquina se ralentiza
- Aparecen advertencias de memoria
- El programa se mata automáticamente

**Soluciones:**

```bash
# Reducir número de hilos
python wifi_bf.py --method brute-force --target PASSWORD \
    --threads 2  # Usar menos paralismo

# Reducir rango de búsqueda
python wifi_bf.py --method brute-force --target PASSWORD \
    --min-length 4 --max-length 6  # Búsqueda más acotada

# En máquinas con poca RAM, usar 1 solo hilo
python wifi_bf.py --method brute-force --target PASSWORD \
    --threads 1
```

---

### Problema: "El programa se congela"

**Síntomas:**
- No hay salida en consola
- El programa aún está en ejecución (según administrador de tareas)

**Causas posibles:**
- Charset muy grande combinado con longitud grande
- Máquina con recursos insuficientes

**Soluciones:**

```bash
# Presionar Ctrl+C para interrumpir
# El programa guardará un checkpoint automáticamente

# Después, reanudar con menos carga
python wifi_bf.py --method brute-force --resume \
    --charset "0123456789"  # Charset más pequeño
    --threads 2  # Menos hilos
```

---

## Consejos de rendimiento

### Optimizar para velocidad máxima

```bash
# En máquina potente con muchos cores
python wifi_bf.py --method brute-force --target PASSWORD \
    --threads 16 \
    --charset "0123456789"  # Charset mínimo
    --min-length 4 --max-length 6  # Rango acotado
```

**Velocidad esperada:** 10,000+ intentos/segundo

### Optimizar para uso de recursos mínimo

```bash
# En máquina débil o en background
python wifi_bf.py --method brute-force --target PASSWORD \
    --threads 2 \
    --charset "0123456789"
    --min-length 5 --max-length 5  # Rango muy específico
```

**Velocidad esperada:** 1,000-5,000 intentos/segundo

---

## FAQ

**P: ¿Puedo usar WiFi-BF en redes de terceros?**

R: NO. Solo en redes propias con autorización explícita. El acceso no autorizado es ilegal.

**P: ¿Qué métodos hay disponibles?**

R: Actualmente `brute-force` está implementado. `dictionary` y `heuristic` vienen próximamente.

**P: ¿Se guarda la contraseña encontrada?**

R: Se guarda una versión parcialmente enmascarada en logs. La contraseña completa está en el reporte con `--show-password` (deshabilitado por defecto por seguridad).

**P: ¿Es más rápido aumentar a 32 hilos?**

R: No necesariamente. El rendimiento depende de CPUs disponibles. Recomendado: hilos ≈ número de núcleos.

**P: ¿Puedo usar otro diccionario?**

R: Sí, cuando `dictionary` esté implementado. Por ahora, solo fuerza bruta.

**P: ¿Los checkpoints se borran automáticamente?**

R: Sí, se eliminan al completar exitosamente. Si no se encuentra, se conservan para reanudar.

---

## Más información

- [README.md](README.md) - Descripción general del proyecto
- [LICENSE](LICENSE) - Terminos de licencia
- Directorio de logs: `logs/`
- Ejemplos: `examples/example_usage.py`

