# Declaración de fuentes, código externo y uso de IA

Proyecto: Sensor de ocupación de estacionamiento · TEI201 · Grupo 10

## 1\. Librerías utilizadas

Todas vienen incluidas en el core ESP32 para Arduino; no se instaló ninguna librería externa.

|Librería|Versión|Uso en el proyecto|Fuente|
|-|-|-|-|
|WiFi.h|core esp32 de Espressif (versión instalada en el IDE: completar desde el Gestor de tarjetas)|Conexión al hotspot (modo estación) y red propia de respaldo (modo AP)|https://github.com/espressif/arduino-esp32|
|WebServer.h|ídem|Página local y endpoint JSON `/estado` en 192.168.4.1|https://github.com/espressif/arduino-esp32|
|HTTPClient.h|ídem|Envío de cada registro a la API de ThingSpeak (`/update`)|https://github.com/espressif/arduino-esp32|
|time.h (NTP)|ídem|Hora real UTC por NTP para el timestamp de cada evento|https://github.com/espressif/arduino-esp32|

Servicios y herramientas: ThingSpeak (MathWorks), plan gratis, API REST de escritura y funciones MATLAB `thingSpeakRead` (https://www.mathworks.com/help/thingspeak/); Python con `matplotlib`, `trimesh`, `manifold3d`, `shapely` y `cadquery` para generar el esquemático y modificar el encapsulado.

## 2\. Código externo adaptado

No se copió código de tutoriales, foros ni repositorios. Las partes basadas en documentación oficial son:

### Envío a ThingSpeak (`enviarRegistro` en `sensor\_estacionamiento.ino`)

* Fuente: documentación de la API "Write Data" de ThingSpeak (parámetros `api\_key`, `field1`…`field8`, `created\_at`).
* Adaptación: se envía por HTTP GET con `HTTPClient`, se agrega `created\_at` con la hora del evento y se valida la respuesta (ThingSpeak responde el número de entrada, o 0 si rechaza la escritura).

### Lectura de datos en MATLAB (`dashboard/\*.m`)

* Fuente: documentación de `thingSpeakRead` de MathWorks.
* Adaptación: lectura del campo 1 de las últimas 24 h y conversión de la hora UTC a la hora de Santiago.

## 3\. Uso de Inteligencia Artificial

Herramienta: **Claude (Anthropic)**, usado entre septiembre y noviembre de 2026 como asistente de programación, diseño y redacción. El equipo definió el problema, eligió y compró los componentes, armó y probó el circuito, tomó todas las mediciones, decidió cada cambio de diseño y verificó cada resultado en el hardware real.

### Firmware completo (`firmware/sensor\_estacionamiento/sensor\_estacionamiento.ino`, v1 a v9)

* Uso: generación del código base y de cada versión a partir de lo que el equipo reportaba en las pruebas.
* Prompts utilizados (resumen): "Código para ESP32 con sensor ultrasónico SR04M-2 que detecte si un espacio está ocupado y muestre el estado en un LED bicolor y una página web"; después, uno por cada falla encontrada (ej.: "el sensor no responde a algunos disparos y eso cambia el estado") y, para la v9, "haz que el ESP32 envíe a ThingSpeak cada cambio de estado con timestamp y un registro cada 30 s".
* Adaptación hecha por el equipo: pines según el montaje real; alimentación del sensor a 3,3 V tras la falla del divisor; calibración con 4 puntos medidos con huincha (real = 1,011 × medida + 4,0); umbrales de 60/80 cm ajustados en la mesa; buzzer pasivo tras descubrir que el activo estaba defectuoso; 100 ms entre disparos y 2 confirmaciones tras medir la velocidad de reacción.
* Comprensión (qué hace cada función):

  * `medirUnaVez()`: manda un pulso de 20 µs por Trig y mide con `pulseIn` cuánto dura el eco; distancia = tiempo × 0,0343 / 2 (velocidad del sonido, ida y vuelta). Devuelve −1 si no hubo eco.
  * `medirMediana()`: hace 5 lecturas, descarta las menores a 20 cm (zona ciega), ordena y toma la mediana para eliminar lecturas erráticas, y aplica la calibración lineal.
  * `sugiereOcupado()`: histéresis: para pasar a ocupado hay que bajar de 60 cm y para volver a libre hay que superar 80 cm, así el estado no parpadea en el borde.
  * `loop()`: el estado cambia solo después de 2 mediciones válidas seguidas que lo sugieran (evita que un peatón cambie el estado) y los ciclos sin respuesta se ignoran.
  * `encolar()` y `atenderNube()`: cada registro se guarda en una cola circular de 30 posiciones con su hora; se envía uno cada 16 s porque el plan gratis de ThingSpeak acepta una escritura cada 15 s. Si el envío falla, el registro queda en la cola y se reintenta.
  * `conectarWifi()`: intenta conectarse 10 s al hotspot; si no puede, crea la red propia "Estacionamiento-A1" (modo AP). Con internet, sincroniza la hora por NTP.
* Verificación: cada versión se cargó y probó en el prototipo con el Monitor Serie; la v9 se verificó viendo llegar los datos al canal de ThingSpeak.

### Visualizaciones del dashboard (`dashboard/1\_estado\_actual.m`, `2\_ocupacion\_por\_hora.m`, `3\_tiempo\_ocupacion.m`)

* Uso: generación de los tres scripts MATLAB.
* Prompt utilizado (resumen): "Scripts MATLAB para ThingSpeak que muestren el estado actual con una alerta de sin cupo, el porcentaje de ocupación por hora y el tiempo promedio de ocupación".
* Adaptación: el equipo eligió los indicadores según el problema del Avance 1, detectó que el gráfico por hora dibujaba una barra de un día de ancho y pidió corregirlo, y dejó fuera una alerta por correo que no aportaba a la demo.
* Comprensión: `1\_estado\_actual` toma el último valor del campo 1 y busca el último registro con el estado contrario para saber desde cuándo está así; si no llegan datos en 2 minutos muestra "SIN DATOS". `2\_ocupacion\_por\_hora` reconstruye el estado minuto a minuto (entre dos registros vale el estado del anterior) y promedia por hora. `3\_tiempo\_ocupacion` detecta los pasos de 0 a 1 y de 1 a 0 y mide la duración de cada ocupación.

### Esquemático (`hardware/esquematico.py`, `esquematico.pdf`)

* Uso: script de Python que dibuja el esquemático a partir de la lista de conexiones verificada por el equipo con una foto del montaje.
* Adaptación: conexiones, valores de resistencias y notas de diseño corresponden al circuito real.

### Lista de materiales (`hardware/BOM.xlsx`)

* Uso: estructura de la tabla y redacción de la justificación técnica de cada componente.
* Adaptación: el equipo aportó los componentes reales, la cotización original y los precios pagados.

### Encapsulado (`diseno-3d/scripts/`: `caja_amplia.py`, `componentes_fusion.py`, `stl_a_step.py`, `ensamble_completo.py`)

* Uso: scripts que modifican el STL de la caja diseñada por el equipo (ranura USB-C, un solo agujero de LED, cuna para el ESP32, caja más amplia) y generan los volúmenes de los componentes para el gemelo 3D.
* Adaptación: el equipo diseñó la caja original, decidió montar el ESP32 con los pines hacia arriba, midió la placa (55 mm de largo) y verificó que todo el hardware entra en la caja impresa.
* Comprensión: la caja se agrandó "estirándola" en planos donde solo hay pared lisa, moviendo todo lo que está más allá del plano; por eso las paredes siguen de 1,6 mm y los agujeros no se deforman, a diferencia de escalar el modelo completo.

### Documentación y presentación (`README.md`, `testing/protocolo\_pruebas.md`)

* Uso: estructura y redacción a partir de los datos, decisiones y resultados del equipo.
* Adaptación: los datos de calibración, tasas de respuesta, fallas y soluciones provienen de las pruebas del equipo; el equipo revisó y corrigió el contenido.

