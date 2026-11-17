# Registro de iteraciones del prototipo

Sensor de ocupación de estacionamiento, TEI201 Grupo 10.

## Prototipo Alpha (Avance 2, 9 de octubre de 2026)

1. **Identificación del sensor.** El sensor comprado es un SR04M-2 (familia AJ-SR04M), no un JSN-SR04T como se indicó en la Entrega 1. Es compatible en modo Trig/Echo.
2. **Montaje con una sola breadboard (400 puntos).** El ESP32 queda fuera de la breadboard y se conecta con cables macho-hembra; la breadboard reparte 3,3 V y GND por los rieles.
3. **Conectividad.** La red de la universidad probablemente bloquea dispositivos IoT. Plan B: si el ESP32 no encuentra la red configurada, crea su propia red WiFi ("Estacionamiento-A1", página en 192.168.4.1). Se corrigió un error en que los reintentos de conexión congelaban el sensor 10 s cada 15 s.
4. **Divisor de voltaje en Echo (1 kΩ / 2 kΩ).** Se instaló para proteger el pin del ESP32. Resultado: el sensor casi nunca respondía. Retirar la 2 kΩ no resolvió el problema.
5. **Alimentación del sensor de 5 V a 3,3 V.** Con el sensor a 3,3 V (rango 3 a 5,5 V) empezó a medir. Se mantuvo la 1 kΩ en serie en Echo. Costo: alcance máximo baja de ~4,5 m a ~3 m.
6. **Buzzer.** El buzzer activo venía defectuoso. Se reemplazó por uno pasivo con un tono de 2 kHz generado con `tone()`.
7. **Zona ciega.** Lecturas falsas de 1,8 a 3,1 cm. Se descartan las lecturas bajo 20 cm.
8. **Lecturas sin respuesta.** Un ciclo sin respuesta ya no cuenta como "libre": se ignora. Tiempo de espera de 70 ms para reconocer el pulso de "nada al frente" (~930 cm).
9. **Velocidad de reacción.** Confirmaciones de 3 a 2 y descanso entre disparos de 60 a 100 ms. Cambio de estado en ~2 s.
10. **Visualización.** El Serial y la página web muestran la última distancia válida y el porcentaje de respuesta del sensor.
11. **Calibración.** Sesgo sistemático de 4 a 5,5 cm. Regresión lineal: real = 1,011 × medida + 4,0 cm (R² = 0,99997). Error medio absoluto de 4,9 a 0,2 cm; validación fuera de muestra a 80 cm con error ≈ +0,8 cm.
12. **Montaje en el encapsulado.** Falso contacto intermitente entre la sonda y su placa al moverla. Solución: asegurar el conector y fijar el cable.

## Prototipo completo (Avance 3, noviembre de 2026)

13. **Persistencia en la nube (firmware v9).** Envío a ThingSpeak (plan gratis) de cada cambio de estado con su hora real (NTP) y un registro periódico cada 30 s. Cola de 30 registros porque el plan gratis acepta 1 escritura cada 15 s; si se cae el WiFi, los registros se suben al volver.
14. **Dashboard.** Canal ThingSpeak con gráficos de los 6 campos, ampolleta en vivo y tres visualizaciones MATLAB: estado actual ("SIN CUPO" / "HAY CUPO"), % de ocupación por hora y tiempo promedio de ocupación. Corrección: el gráfico por hora dibujaba una barra de un día de ancho con una sola hora de datos; ahora muestra siempre 24 barras.
15. **Encapsulado v2.** Se reemplazó el hueco grande de la pared por una ranura USB-C de 13 × 8 mm, se dejó un solo agujero de LED (el LED bicolor usa uno) y se agregó una cuna para el ESP32 montado con los pines hacia arriba, para que los cables no se aplasten.
16. **Encapsulado amplio.** La protoboard no cabía y no se pudieron acortar los cables soldándolos. La caja se agrandó de 123 × 89 × 40 a 163 × 119 × 50 mm estirando el modelo solo en zonas de pared lisa, sin escalar: paredes de 1,6 mm y agujeros del mismo tamaño.

17. **Montaje final en la caja.** El buzzer va en el agujero de la pared derecha y el LED en el agujero frontal. Los cables, que no se pudieron acortar, se ordenaron con amarras plásticas, y algunos módulos se fijaron con huincha aislante.
18. **Soporte de demostración.** Base de MDF de 30 × 30 cm y tubo PVC de 25 mm unido con bujes, sin pegamento, para mostrar la caja a la altura del parachoques (~40 cm), como iría en un poste.
19. **Gemelo 3D en Fusion 360.** Ensamble de la caja con volúmenes de todos los componentes en su posición real. Inspección de interferencias: ninguna en 15 cuerpos. Renders y planos con cotas y tolerancias.

## Pendientes y mejoras propuestas

- Correr las pruebas P2, P3, P4, P6, P7 y P8 del protocolo (`protocolo_pruebas.md`).
- Condensador de 10 a 470 µF entre VCC y GND del sensor para subir la tasa de respuesta (59 a 64 %).
- Fijaciones desmontables (clips impresos o tornillos) para los módulos, en lugar de la huincha.
- Caja IP65 con prensaestopas para la versión de campo.
