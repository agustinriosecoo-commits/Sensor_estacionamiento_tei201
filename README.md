# Sensor de ocupación de estacionamiento (TEI201, Grupo 10)

Dispositivo IoT que detecta si un espacio de estacionamiento está libre u ocupado con un sensor ultrasónico impermeable, muestra el estado en un LED y sube cada cambio a la nube (ThingSpeak). Un dashboard en línea muestra el estado en vivo, el histórico, el % de ocupación por hora y el tiempo promedio de ocupación, para que el conductor sepa si hay cupo **antes de llegar**.

**Dashboard:** https://thingspeak.mathworks.com/channels/3580318

## Integrantes

- Pablo Rojas
- Felipe Blanco
- Agustín Rioseco

Profesor: Camilo Vásquez Wilson · Taller de Diseño en Ingeniería (TEI201) · Universidad Adolfo Ibáñez · 2026

## Problema (Avance 1)

En el corredor Alameda-Estación Central se aprobaron más de 35 mil viviendas entre 2012 y 2021, pero se construyeron menos de un tercio de esa cantidad en estacionamientos (Ahumada, 2026). Los conductores que llegan en horario de entrada y salida laboral dan vueltas buscando dónde estacionar (*cruising for parking*), lo que genera congestión, tiempo perdido y emisiones sin aportar al desplazamiento (Shoup, 2007). Las soluciones con cámaras dependen de buena iluminación y son caras para la vía pública (García Guerrero, 2022). Este proyecto propone sensores ultrasónicos de bajo costo, robustos a la intemperie y conectados a la nube.

## Cómo funciona

```
Sensor SR04M-2 ──distancia──▶ ESP32 ──estado──▶ LED verde/rojo + buzzer
                              │  mediana de 5 lecturas, calibración,
                              │  histéresis (60/80 cm) y confirmación
                              │
                              └──WiFi (HTTP)──▶ ThingSpeak ──▶ Dashboard (web/celular)
                                 cada cambio con su hora real + registro cada 30 s
```

- **Frecuencia de muestreo:** el sensor mide cada ~0,5 s para que el LED reaccione en ~2 s. A la nube se envía cada cambio de estado apenas se confirma y un registro periódico cada 30 s: un auto tarda minutos en estacionarse, así que muestrear más seguido no agrega información. Con esto se usan ~1,1 millones de mensajes al año, bajo el límite gratis de ThingSpeak (3 millones).
- **Respaldo:** si se cae el WiFi, una cola guarda hasta 30 registros (~8 min) y los sube al volver. Si al encender no hay red, el ESP32 crea su propia red "Estacionamiento-A1" con una página local en 192.168.4.1.

## Estructura del repositorio

```
├── README.md
├── FUENTES.md                  Librerías, código externo y uso de IA
├── firmware/
│   └── sensor_estacionamiento/
│       ├── sensor_estacionamiento.ino   Firmware v9
│       └── secretos_ejemplo.h           Plantilla de credenciales
├── dashboard/                  Visualizaciones MATLAB de ThingSpeak
├── hardware/
│   ├── esquematico.pdf / .png  Esquemático del circuito
│   └── BOM.xlsx                Lista de materiales con costos y justificación
├── diseno-3d/
│   ├── caja_base_amplia.stl    Base para imprimir
│   ├── caja_tapa_amplia.stl    Tapa para imprimir
│   ├── componentes.step        Volúmenes de los componentes (gemelo 3D)
│   └── encapsulado.f3d, renders/, planos.pdf   Modelo en Fusion 360
├── testing/
│   ├── protocolo_pruebas.md    Protocolo de pruebas y validación
│   ├── iteraciones_prototipo.md
│   └── datos/                  Datos de calibración y exportaciones de ThingSpeak
└── docs/
    └── avance1_informe.pdf
```

## Componentes para replicar el hardware

| Componente | Cantidad |
|---|---|
| ESP32 DevKit (WROOM-32, USB-C, 38 pines) | 1 |
| Sensor ultrasónico impermeable SR04M-2 (AJ-SR04M) | 1 |
| Módulo LED bicolor rojo/verde | 1 |
| Módulo buzzer pasivo | 1 |
| Resistencias 220 Ω | 2 |
| Resistencia 1 kΩ | 1 |
| Protoboard 400 puntos y cables jumper | 1 + set |
| Caja impresa en 3D (PLA) y 4 tornillos M3 | 1 |

Costo total estimado: **$33.750 CLP** (detalle en `hardware/BOM.xlsx`).

### Conexiones

| Desde | Hacia |
|---|---|
| Sensor VCC / GND | 3V3 / GND |
| Sensor RX (Trig) | D5 |
| Sensor TX (Echo) | resistencia 1 kΩ en serie → D18 |
| LED S (verde) | 220 Ω → D25 |
| LED medio (rojo) | 220 Ω → D26 |
| LED − | GND |
| Buzzer S / medio / − | D27 / 3V3 / GND |

El sensor se alimenta a 3,3 V para que sus señales queden al nivel lógico del ESP32.

## Cargar el firmware

1. Instalar Arduino IDE y el core **esp32** de Espressif (Gestor de tarjetas). No se necesitan librerías externas.
2. Abrir `firmware/sensor_estacionamiento/sensor_estacionamiento.ino`.
3. Copiar `secretos_ejemplo.h` como `secretos.h` en la misma carpeta y completar la red WiFi y la Write API Key del canal de ThingSpeak.
4. Elegir la placa **ESP32 Dev Module**, el puerto, y cargar.
5. Abrir el Monitor Serie a 115200 baudios: debe decir `WiFi OK`, `Hora NTP OK` y después `nube=ok`.

## Conectar el dashboard

1. Crear un canal en ThingSpeak con 6 campos: `ocupado`, `distancia_cm`, `tipo_registro`, `respuesta_pct`, `cambios`, `uptime_s`.
2. En **Apps → MATLAB Visualizations → New → Custom**, pegar cada script de `dashboard/`, completar `CANAL_ID` y `READ_KEY` y agregarlo a la vista del canal.
3. Agregar un widget **Lamp Indicator** sobre el Field 1 (se enciende cuando el espacio está ocupado).

## Resultados principales

- Error medio de la distancia: 4,9 cm sin calibrar, 0,2 cm calibrado (validación fuera de muestra: +0,8 cm).
- Cambio de estado local en ~2 s.
- Tasa de respuesta del sensor: 59 a 64 % de los disparos, compensada con la mediana de 5 lecturas.
- Protocolo completo y resultados en `testing/protocolo_pruebas.md`.

## Fuentes

- Ahumada, S. (2026, 10 de abril). La deuda de la Alameda con Estación Central. *El Mostrador*.
- García Guerrero, C. del C. (2022). *Diseño de un sistema inteligente para la detección de plazas de estacionamientos libres* [Tesis de pregrado, Universidad de Chile].
- Shoup, D. (2007). Cruising for parking. *Access, 30*, 16–22.

Declaración de librerías, código externo y uso de IA: ver [`FUENTES.md`](FUENTES.md).
