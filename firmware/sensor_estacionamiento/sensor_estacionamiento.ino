/*
  Sensor de ocupación de estacionamiento (TEI201, Grupo 10), versión 9
  Prototipo IoT: sensor -> procesamiento -> actuador -> conectividad -> NUBE

  Novedad v9: persistencia en ThingSpeak (plan gratis).
    - Cada cambio de estado se registra con su timestamp real (hora NTP, UTC).
    - Además, un registro periódico cada 30 s (latido del sistema).
    - Los registros pasan por una cola: el plan gratis acepta 1 escritura cada 15 s
      por canal, así que se envía 1 cada 16 s. Como cada registro lleva su propia
      hora (created_at), un envío atrasado no deforma el histórico.
    - Si se cae el WiFi, la cola guarda hasta 30 registros y los sube al volver.
    - Si al encender no hay red, el ESP32 crea su propia red (modo AP) como antes:
      LED, buzzer y página local funcionan, pero sin nube (no hay internet).

  Canal ThingSpeak (crear en thingspeak.mathworks.com > Channels > New Channel):
    field1 = ocupado (1/0)
    field2 = distancia calibrada (cm)
    field3 = tipo de registro (1 = cambio de estado, 0 = periódico)
    field4 = tasa de respuesta del sensor (%)
    field5 = cambios de estado acumulados
    field6 = tiempo encendido (s)
  La Write API Key (pestaña "API Keys") va en secretos.h.

  Hardware:
    - ESP32 DevKit (USB-C)
    - Sensor ultrasónico impermeable SR04M-2 en modo 1 (Trig/Echo)
    - Módulo LED bicolor rojo/verde
    - Módulo buzzer PASIVO, suena con tone()
    Sensor alimentado a 3,3 V. Echo pasa por una resistencia de 1 kΩ en serie.

  Lógica de detección (sin cambios respecto de v8):
    1. Cada ~0,5 s se toman 5 lecturas y se usa la mediana.
    2. Histéresis: OCUPADO bajo 60 cm, LIBRE sobre 80 cm.
    3. Confirmación: el estado cambia tras 2 mediciones válidas seguidas.
    4. LED verde = libre, rojo = ocupado; pitido en cada cambio.

  Librerías: WiFi.h, WebServer.h, HTTPClient.h y time.h vienen con el core ESP32
  de Arduino, no hay que instalar nada.
*/

#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <time.h>
#include "secretos.h"   // WIFI_SSID, WIFI_PASS, TS_WRITE_KEY (no se sube al repo)

// Red propia del ESP32 si no encuentra la del hotspot (la clave necesita mínimo 8 caracteres)
const char* AP_SSID = "Estacionamiento-A1";
const char* AP_PASS = "tei201g10";

// ---------- Pines ----------
const int PIN_TRIG      = 5;
const int PIN_ECHO      = 18;
const int PIN_LED_VERDE = 25;
const int PIN_LED_ROJO  = 26;
const int PIN_BUZZER    = 27;

// ---------- Parámetros de detección ----------
const float UMBRAL_OCUPADO_CM = 60.0;
const float UMBRAL_LIBRE_CM   = 80.0;
const int   CONFIRMACIONES    = 2;
const int   N_MUESTRAS        = 5;
const unsigned long TIMEOUT_ECO_US = 70000UL;
const float DIST_MIN_CM       = 20.0;
const int   FRECUENCIA_BUZZER_HZ = 2000;

// ---------- Calibración lineal: distancia_real = CAL_PENDIENTE * medida + CAL_OFFSET_CM ----------
const float CAL_PENDIENTE = 1.011;
const float CAL_OFFSET_CM = 4.0;

// ---------- Nube (ThingSpeak) ----------
// Registro periódico cada 30 s: un auto tarda minutos en estacionarse, así que muestrear
// más seguido no agrega información. Los cambios de estado NO esperan este periodo:
// se registran apenas se confirman (~2 s), con su hora exacta.
// Consumo: 2.880 periódicos/día + cambios ≈ 1,1 millones/año, bajo el tope gratis de 3 millones.
const unsigned long PERIODO_REGISTRO_MS = 30000UL;
const unsigned long INTERVALO_ENVIO_MS  = 16000UL;   // límite del plan gratis (15 s) + 1 s de margen
const int COLA_MAX = 30;                              // ~8 min de registros si se cae el WiFi

struct Registro {
  time_t ts;              // hora UTC (0 si aún no hay hora NTP)
  bool ocupado;
  float dist;             // -1 = sin lectura válida
  uint8_t tipo;           // 1 = cambio, 0 = periódico
  int respuestaPct;
  unsigned long cambios;
  unsigned long uptime;
};

Registro cola[COLA_MAX];
int colaIni = 0, colaN = 0;
unsigned long registrosPerdidos = 0, enviosOk = 0, enviosFallidos = 0;
unsigned long ultimoPeriodico = 0, ultimoEnvio = 0;
bool hayEnvioPrevio = false;
bool nubeOk = false;

// ---------- Estado global ----------
WebServer server(80);
bool  ocupado = false;
float ultimaDistancia = -1;
float ultimaValida = -1;
unsigned long ciclosTotales = 0, ciclosSinRespuesta = 0;
int   contadorCambio = 0;
unsigned long cambiosTotales = 0;
bool  modoAP = false;

// =====================================================================
//  Sensor
// =====================================================================

float medirUnaVez() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(5);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(20);
  digitalWrite(PIN_TRIG, LOW);

  unsigned long duracion = pulseIn(PIN_ECHO, HIGH, TIMEOUT_ECO_US);
  if (duracion == 0) return -1;
  return duracion * 0.0343f / 2.0f;
}

float medirMediana() {
  float v[N_MUESTRAS];
  int n = 0;
  for (int i = 0; i < N_MUESTRAS; i++) {
    float d = medirUnaVez();
    if (d >= DIST_MIN_CM) v[n++] = d;
    delay(100);
  }
  if (n == 0) return -1;
  for (int i = 0; i < n - 1; i++)
    for (int j = i + 1; j < n; j++)
      if (v[j] < v[i]) { float t = v[i]; v[i] = v[j]; v[j] = t; }
  float mediana = v[n / 2];
  if (mediana > 400) return mediana;
  return CAL_PENDIENTE * mediana + CAL_OFFSET_CM;
}

bool sugiereOcupado(float d) {
  if (d < 0) return ocupado;
  if (ocupado) return d < UMBRAL_LIBRE_CM;
  return d < UMBRAL_OCUPADO_CM;
}

int respuestaPct() {
  return ciclosTotales ? (int)(100 * (ciclosTotales - ciclosSinRespuesta) / ciclosTotales) : 0;
}

// =====================================================================
//  Actuadores
// =====================================================================

void mostrarEstado() {
  digitalWrite(PIN_LED_ROJO,  ocupado ? HIGH : LOW);
  digitalWrite(PIN_LED_VERDE, ocupado ? LOW  : HIGH);
}

void pitido(int ms) {
  tone(PIN_BUZZER, FRECUENCIA_BUZZER_HZ, ms);
  delay(ms);
  noTone(PIN_BUZZER);
}

void autoTest() {
  digitalWrite(PIN_LED_ROJO, HIGH);  delay(400); digitalWrite(PIN_LED_ROJO, LOW);
  digitalWrite(PIN_LED_VERDE, HIGH); delay(400); digitalWrite(PIN_LED_VERDE, LOW);
  pitido(100);
}

// =====================================================================
//  Nube: cola de registros y envío a ThingSpeak
// =====================================================================

// Agrega un registro a la cola. Si está llena, se descarta el más antiguo.
void encolar(uint8_t tipo) {
  if (modoAP) return;                         // sin internet no tiene sentido acumular
  Registro r;
  r.ts = time(nullptr);
  r.ocupado = ocupado;
  r.dist = ultimaValida;
  r.tipo = tipo;
  r.respuestaPct = respuestaPct();
  r.cambios = cambiosTotales;
  r.uptime = millis() / 1000;

  if (colaN == COLA_MAX) {
    colaIni = (colaIni + 1) % COLA_MAX;
    colaN--;
    registrosPerdidos++;
  }
  cola[(colaIni + colaN) % COLA_MAX] = r;
  colaN++;
}

// Envía un registro. ThingSpeak responde con el número de entrada (>0) si lo aceptó,
// o "0" si lo rechazó (por ejemplo, por escribir antes de 15 s).
bool enviarRegistro(const Registro& r) {
  String url = "http://api.thingspeak.com/update?api_key=";
  url += TS_WRITE_KEY;
  url += "&field1="; url += r.ocupado ? 1 : 0;
  if (r.dist >= 0) { url += "&field2="; url += String(r.dist, 1); }
  url += "&field3="; url += r.tipo;
  url += "&field4="; url += r.respuestaPct;
  url += "&field5="; url += r.cambios;
  url += "&field6="; url += r.uptime;

  // Hora real del evento (solo si el reloj ya se sincronizó por NTP: año > 2023)
  if (r.ts > 1700000000) {
    struct tm t;
    gmtime_r(&r.ts, &t);
    char buf[25];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &t);
    url += "&created_at="; url += buf;
  }

  HTTPClient http;
  http.setTimeout(4000);
  http.begin(url);
  int codigo = http.GET();
  String cuerpo = (codigo == 200) ? http.getString() : "";
  http.end();
  return codigo == 200 && cuerpo.toInt() > 0;
}

// Envía el registro más antiguo de la cola si ya pasó el intervalo mínimo.
void atenderNube() {
  if (modoAP || WiFi.status() != WL_CONNECTED || colaN == 0) return;
  if (hayEnvioPrevio && millis() - ultimoEnvio < INTERVALO_ENVIO_MS) return;

  ultimoEnvio = millis();
  hayEnvioPrevio = true;
  if (enviarRegistro(cola[colaIni])) {
    colaIni = (colaIni + 1) % COLA_MAX;
    colaN--;
    enviosOk++;
    nubeOk = true;
  } else {
    enviosFallidos++;                         // queda en la cola y se reintenta en 16 s
    nubeOk = false;
  }
}

// =====================================================================
//  Conectividad local
// =====================================================================

void conectarWifi() {
  Serial.printf("Conectando a WiFi \"%s\"...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 10000) delay(250);

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi OK. Abrir en el celular: http://");
    Serial.println(WiFi.localIP());

    // Reloj por NTP en UTC (ThingSpeak muestra la hora en la zona configurada en el canal)
    configTime(0, 0, "pool.ntp.org", "time.google.com");
    unsigned long t1 = millis();
    while (time(nullptr) < 1700000000 && millis() - t1 < 5000) delay(200);
    Serial.println(time(nullptr) > 1700000000 ? "Hora NTP OK" : "Sin hora NTP aún (se usará la hora de llegada)");
  } else {
    WiFi.disconnect(true);
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASS);
    modoAP = true;
    Serial.printf("Sin red externa. Red propia creada: \"%s\" (clave %s). SIN NUBE.\n", AP_SSID, AP_PASS);
    Serial.print("Conectar el celular a esa red y abrir: http://");
    Serial.println(WiFi.softAPIP());
  }
}

void handleEstado() {
  String json = "{\"ocupado\":";
  json += ocupado ? "true" : "false";
  json += ",\"distancia_cm\":";
  json += (ultimaValida < 0) ? String("null") : String(ultimaValida, 1);
  json += ",\"respuesta_pct\":";  json += respuestaPct();
  json += ",\"cambios\":";        json += cambiosTotales;
  json += ",\"uptime_s\":";       json += millis() / 1000;
  json += ",\"nube\":\"";         json += modoAP ? "sin internet" : (nubeOk ? "ok" : "pendiente");
  json += "\",\"en_cola\":";      json += colaN;
  json += ",\"envios_ok\":";      json += enviosOk;
  json += "}";
  server.send(200, "application/json", json);
}

const char PAGINA[] PROGMEM = R"HTML(
<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Estacionamiento</title>
<style>
 body{font-family:system-ui,sans-serif;margin:0;display:flex;flex-direction:column;
      align-items:center;justify-content:center;min-height:100vh;background:#f4f1ea;color:#1d2b22}
 #caja{width:80vw;max-width:340px;padding:40px 0;border-radius:20px;text-align:center;
       color:#fff;font-size:2.2rem;font-weight:700;transition:background .3s}
 .libre{background:#2e7d4f} .ocupado{background:#b3362c} .sin{background:#888}
 p{margin:8px}
</style></head><body>
<h2>Espacio A1</h2>
<div id="caja" class="sin">...</div>
<p id="dist">Distancia: --</p>
<p id="info"></p>
<p id="nube"></p>
<script>
async function act(){
  try{
    const r = await fetch('/estado'); const d = await r.json();
    const c = document.getElementById('caja');
    c.className = d.ocupado ? 'ocupado' : 'libre';
    c.textContent = d.ocupado ? 'OCUPADO' : 'LIBRE';
    document.getElementById('dist').textContent =
      'Distancia: ' + (d.distancia_cm === null ? '--' : (d.distancia_cm > 400 ? 'nada al frente' : d.distancia_cm + ' cm')) +
      ' · Respuesta del sensor: ' + d.respuesta_pct + '%';
    document.getElementById('info').textContent =
      'Cambios: ' + d.cambios + ' · Encendido hace ' + d.uptime_s + ' s';
    document.getElementById('nube').textContent =
      'Nube: ' + d.nube + ' · En cola: ' + d.en_cola + ' · Enviados: ' + d.envios_ok;
  }catch(e){
    const c = document.getElementById('caja'); c.className='sin'; c.textContent='Sin conexión';
  }
}
setInterval(act, 1000); act();
</script></body></html>
)HTML";

void handleRaiz() { server.send_P(200, "text/html", PAGINA); }

// =====================================================================
//  Setup y loop
// =====================================================================

void setup() {
  Serial.begin(115200);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_LED_VERDE, OUTPUT);
  pinMode(PIN_LED_ROJO, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_TRIG, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  autoTest();
  conectarWifi();

  server.on("/", handleRaiz);
  server.on("/estado", handleEstado);
  server.begin();

  mostrarEstado();
  ultimoPeriodico = millis();
}

void loop() {
  server.handleClient();

  // 1. Medir
  ultimaDistancia = medirMediana();
  ciclosTotales++;
  if (ultimaDistancia < 0) ciclosSinRespuesta++;
  else ultimaValida = ultimaDistancia;

  // 2. Decidir con histéresis + confirmación
  if (ultimaDistancia < 0) {
    // sin información en este ciclo
  } else if (sugiereOcupado(ultimaDistancia) != ocupado) {
    contadorCambio++;
    if (contadorCambio >= CONFIRMACIONES) {
      ocupado = !ocupado;
      contadorCambio = 0;
      cambiosTotales++;
      mostrarEstado();
      encolar(1);                     // registro de CAMBIO con su hora exacta
      pitido(ocupado ? 150 : 60);
    }
  } else {
    contadorCambio = 0;
  }

  // 3. Registro periódico cada 30 s
  if (millis() - ultimoPeriodico >= PERIODO_REGISTRO_MS) {
    ultimoPeriodico += PERIODO_REGISTRO_MS;
    encolar(0);
  }

  // 4. Subir a la nube (máximo 1 envío cada 16 s)
  atenderNube();

  // 5. Log por Serial
  const char* red = modoAP ? "propia" : (WiFi.status() == WL_CONNECTED ? "externa" : "caida");
  Serial.printf("dist=%.1f cm%s  estado=%s  respuesta=%d%%  red=%s  nube=%s  cola=%d  ok=%lu  fallidos=%lu  perdidos=%lu\n",
                ultimaValida, ultimaDistancia < 0 ? " (sin respuesta)" : "",
                ocupado ? "OCUPADO" : "LIBRE", respuestaPct(), red,
                modoAP ? "-" : (nubeOk ? "ok" : "pend"), colaN, enviosOk, enviosFallidos, registrosPerdidos);
}
