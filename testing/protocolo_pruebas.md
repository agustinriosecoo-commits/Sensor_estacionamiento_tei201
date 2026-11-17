# Protocolo de pruebas y validación

Sensor de ocupación de estacionamiento · TEI201 · Grupo 10
Versión del sistema: firmware v9 (ESP32 + SR04M-2 + ThingSpeak) · Noviembre 2026

## 1. Objetivo general

Comprobar que el dispositivo detecta de forma confiable si un espacio de estacionamiento está libre u ocupado, que esa información llega a la nube y al dashboard a tiempo para que un conductor la use antes de llegar, y que el sistema funciona de forma continua. Cada prueba responde a un requerimiento o supuesto definido en el Avance 1:

| Requerimiento o supuesto del Avance 1 | Prueba que lo valida |
|---|---|
| Precisión del sensor a distintas distancias | P1 |
| Precisión a distintos ángulos de instalación | P3 |
| Comunicar en tiempo real el estado de ocupación | P4, P8 |
| Detección confiable (sin alertas falsas) | P2 |
| Operación estable y continua | P5, P6 |
| Cobertura de conectividad | P7 |
| Costo compatible con escalar a muchos espacios | P9 |

## 2. Condiciones generales

- Montaje: caja cerrada, sensor apuntando horizontal hacia el "espacio", a la altura del parachoques (~40 cm).
- Superficie que simula un auto: caja de cartón de al menos 50 × 50 cm o un auto real cuando sea posible.
- Umbrales del firmware: OCUPADO bajo 60 cm, LIBRE sobre 80 cm, cambio tras 2 mediciones válidas seguidas. (En la demo de mesa; en terreno se ajustan al ancho real del espacio.)
- Conectividad: hotspot del celular (la red de la universidad bloquea dispositivos IoT).
- Instrumentos: huincha de medir, cronómetro del celular o video a 30 fps, Monitor Serie (115200 baudios), canal ThingSpeak "Estacionamiento A1" (exportable a CSV).
- Toda prueba guarda su evidencia en `testing/datos/` (CSV de ThingSpeak, logs del Monitor Serie, fotos o video).

## 3. Pruebas

### P1. Precisión de la distancia medida

- **Objetivo:** cuantificar el error del sensor y verificar la calibración lineal (real = 1,011 × medida + 4,0 cm).
- **Procedimiento:**
  1. Poner un objeto plano a 30, 60, 80, 100 y 150 cm de la cara de la sonda, medidos con huincha.
  2. En cada distancia, anotar 10 lecturas del Monitor Serie.
  3. Calcular el error medio absoluto y la desviación estándar por distancia.
- **Criterio de éxito:** error medio absoluto ≤ 1 cm (precisión de fábrica) y repetibilidad ≤ ±1 cm en cada distancia.
- **Estado:** realizada (iteración 11). Error medio de 4,9 cm sin calibrar a 0,2 cm calibrado; validación fuera de muestra a 80 cm con error ≈ +0,8 cm. **Cumple.**

### P2. Exactitud de la detección y falsos positivos

- **Objetivo:** medir qué porcentaje de llegadas y salidas se detectan bien, y que un peatón que pasa no marque "ocupado".
- **Procedimiento:**
  1. Simular 20 llegadas y 20 salidas (poner y sacar la caja) y anotar si el LED y el Field 1 cambian correctamente.
  2. Hacer pasar una persona caminando por delante del sensor 20 veces, sin detenerse.
  3. Dejar el espacio vacío 30 minutos y contar cambios de estado espurios.
- **Métricas:** exactitud = detecciones correctas / 40; tasa de falsos positivos = cambios espurios / 20 pasadas.
- **Criterio de éxito:** exactitud ≥ 95 % (al menos 38 de 40) y como máximo 1 falso positivo en 20 pasadas; 0 cambios con el espacio vacío.

### P3. Ángulo de instalación

- **Objetivo:** verificar que la detección se mantiene si el sensor o el auto no quedan perfectamente de frente.
- **Procedimiento:** con la caja a 50 cm, girarla 0°, 15°, 30° y 45° respecto del eje del sensor; 10 llegadas en cada ángulo.
- **Criterio de éxito:** ≥ 9 de 10 detecciones correctas hasta 30°. Se registra a partir de qué ángulo falla, como límite de instalación.

### P4. Latencia de extremo a extremo

- **Objetivo:** medir cuánto tarda un cambio físico en verse en el LED y en el dashboard.
- **Procedimiento:**
  1. Grabar en un mismo video el sensor y la pantalla con el dashboard (Field 1 y ampolleta).
  2. Hacer 10 cambios de estado separados por al menos 20 s.
  3. Medir, cuadro a cuadro, el tiempo desde el cambio físico hasta (a) el cambio del LED y (b) el cambio en el dashboard.
- **Criterio de éxito:** LED en ≤ 3 s en 10 de 10 casos; dashboard en ≤ 20 s en al menos 9 de 10 casos.
- **Nota:** el plan gratis de ThingSpeak acepta 1 escritura cada 15 s, así que el piso teórico de la nube es de ~16 s cuando hay dos cambios seguidos. El timestamp de cada registro es la hora real del evento (NTP), así que el histórico no se atrasa aunque el envío sí.

### P5. Tasa de respuesta del sensor

- **Objetivo:** cuantificar cuántos disparos responde el sensor y comprobar que eso no afecta la detección.
- **Procedimiento:** con el sistema encendido 1 hora, leer el Field 4 (respuesta %) y contar ciclos sin respuesta.
- **Criterio de éxito:** respuesta ≥ 55 % y ningún cambio de estado causado por ciclos sin respuesta (el firmware los ignora).
- **Estado:** medido en el prototipo Alpha: 59 a 64 % a 3,3 V. Mejora propuesta: condensador de 10 a 470 µF entre VCC y GND del sensor.

### P6. Prueba larga de continuidad (8 horas)

- **Objetivo:** verificar que el sistema funciona sin interrupciones y genera histórico real.
- **Procedimiento:**
  1. Dejar el sistema encendido 8 horas con el hotspot o WiFi doméstico.
  2. Exportar el canal de ThingSpeak a CSV.
  3. Contar registros periódicos recibidos (esperados: 8 h × 120 = 960), reinicios (el Field 6, uptime, vuelve a cero) y registros perdidos (contador del Monitor Serie).
- **Criterio de éxito:** ≥ 98 % de los registros periódicos esperados, 0 reinicios, 0 registros perdidos.

### P7. Conectividad y respaldo

- **Objetivo:** comprobar que un corte de internet no pierde datos y que existe un modo de respaldo.
- **Procedimiento:**
  1. Con el sistema enviando datos, apagar el hotspot 3 minutos, provocar 2 cambios de estado y volver a encenderlo.
  2. Verificar en ThingSpeak que los registros del corte aparecen con su hora correcta.
  3. Encender el ESP32 sin hotspot y verificar que crea la red "Estacionamiento-A1" y que la página 192.168.4.1 muestra el estado.
- **Criterio de éxito:** 100 % de los registros del corte recuperados (la cola guarda hasta 30, unos 8 minutos); modo AP operativo en ≤ 15 s desde el encendido.

### P8. Validación contra el problema (escenario de hora peak)

- **Objetivo:** demostrar que el sistema entrega información útil para decidir, que es el problema del Avance 1: el conductor sabe si hay cupo antes de llegar y deja de dar vueltas (cruising).
- **Procedimiento:**
  1. Simular una "hora peak" de 30 minutos con 6 llegadas y salidas a intervalos irregulares.
  2. Un integrante, sin ver el espacio, consulta el dashboard desde su celular con datos móviles cada 2 minutos y anota si cree que hay cupo.
  3. Comparar sus respuestas con el estado real y revisar los indicadores: estado actual, % de ocupación por hora y tiempo promedio de ocupación.
- **Criterio de éxito:** ≥ 95 % de coincidencia entre lo que indica el dashboard y el estado real; los indicadores reflejan la hora peak simulada.

### P9. Costo por espacio

- **Objetivo:** verificar que el costo unitario permite escalar a un corredor.
- **Procedimiento:** sumar el BOM (`hardware/BOM.xlsx`) y separar el costo por espacio (sensor, ESP32, caja) del costo compartido.
- **Criterio de éxito:** costo por espacio menor que el de una solución con cámara y procesamiento por visión (referencia del Avance 1).

## 4. Fallas encontradas y cómo se resolvieron

| Falla | Causa | Solución | Resultado |
|---|---|---|---|
| El sensor casi nunca respondía (lecturas en 0) | Con el divisor 1 kΩ / 2 kΩ en Echo y el sensor a 5 V, la señal quedaba en el límite | Sensor alimentado a 3,3 V y solo 1 kΩ en serie en Echo | El sensor empezó a medir (alcance baja de ~4,5 a ~3 m) |
| Lecturas erráticas y ciclos sin respuesta cambiaban el estado | El sensor no responde a parte de los disparos | Mediana de 5 lecturas, 100 ms entre disparos y ciclos sin respuesta ignorados | Cambio de estado estable en ~2 s |
| Lecturas falsas de 1,8 a 3,1 cm | Zona ciega de la sonda | Se descartan lecturas bajo 20 cm | Sin falsos "ocupado" por ruido |
| Sensor dejó de detectar al montarlo en la caja | Falso contacto entre sonda y placa | Asegurar el conector y fijar el cable | Detección restablecida |
| Buzzer sin sonido | Buzzer activo defectuoso | Reemplazo por buzzer pasivo con tone() a 2 kHz | Funciona |

## 5. Limitaciones conocidas

- La caja impresa en PLA no es hermética (ranura USB-C, agujero del LED): la prueba de humedad del Avance 1 queda para la versión de campo con caja IP65 y prensaestopas.
- La demo de mesa usa umbrales de 60/80 cm; en terreno se recalibran según la geometría real del espacio.
- Un sensor representa un solo espacio; la alerta "sin cupo" de un sector se obtiene al sumar varios dispositivos.

## 6. Registro de resultados

| Prueba | Fecha | Resultado | ¿Cumple? | Evidencia |
|---|---|---|---|---|
| P1 | 09-10-2026 | Error medio 0,2 cm (en muestra), +0,8 cm (fuera de muestra) | Sí | `datos/calibracion.csv` |
| P2 | | | | |
| P3 | | | | |
| P4 | | | | |
| P5 | 09-10-2026 | 59 a 64 % de respuesta | Sí | log del Monitor Serie |
| P6 | | | | |
| P7 | | | | |
| P8 | | | | |
| P9 | | | | |
