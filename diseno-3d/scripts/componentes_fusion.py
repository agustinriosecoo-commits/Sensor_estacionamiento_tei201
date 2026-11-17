"""Gemelo 3D: volúmenes referenciales de los componentes, en las coordenadas de caja_base_amplia.stl.
Genera componentes.step (un componente con nombre y color por pieza) para abrir en Fusion 360,
y caja_tapa_ensamble.stl (la tapa girada y puesta sobre la base, para el ensamble).
Medidas en mm. Ejes: x = largo de la caja, y = ancho (y = 0 es la pared del sensor), z = alto.
"""
import cadquery as cq
import numpy as np
import trimesh


def caja(x0, y0, z0, x1, y1, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cilindro_y(cx, cz, r, y0, y1):
    """Cilindro con eje a lo largo de y."""
    return cq.Workplane('XZ').circle(r).extrude(-(y1 - y0)).translate((cx, y0, cz))


def cilindro_x(cy, cz, r, x0, x1):
    """Cilindro con eje a lo largo de x."""
    return cq.Workplane('YZ').circle(r).extrude(x1 - x0).translate((x0, cy, cz))


def cilindro_z(cx, cy, r, z0, z1):
    return cq.Workplane('XY').circle(r).extrude(z1 - z0).translate((cx, cy, z0))


piezas = {
    # ESP32 dado vuelta en la cuna (PCB sobre las repisas a z = 7,5)
    'ESP32_PCB':        (caja(1.6, 12.0, 7.5, 56.6, 40.0, 9.1), (0.12, 0.42, 0.25)),
    'ESP32_modulo':     (caja(37.0, 13.25, 4.4, 55.0, 38.75, 7.5), (0.55, 0.55, 0.55)),
    'ESP32_USB_C':      (caja(1.6, 21.5, 4.3, 9.0, 30.5, 7.5), (0.75, 0.75, 0.75)),
    'ESP32_pines_A':    (caja(3.0, 12.2, 9.1, 55.0, 14.74, 17.6), (0.1, 0.1, 0.1)),
    'ESP32_pines_B':    (caja(3.0, 37.26, 9.1, 55.0, 39.8, 17.6), (0.1, 0.1, 0.1)),
    # Protoboard de 400 puntos
    'Protoboard_400':   (caja(62.0, 30.5, 1.6, 144.5, 85.0, 10.1), (0.95, 0.95, 0.92)),
    # Cable de la sonda enrollado contra la pared trasera (con amarra)
    'Cable_sonda':      (caja(18.0, 96.0, 1.6, 132.0, 114.0, 11.6), (0.08, 0.08, 0.08)),
    # Placa de control del sensor SR04M-2 y su sonda (eje de la sonda en el agujero frontal)
    'Sensor_placa':     (caja(6.0, 50.0, 1.6, 47.0, 78.5, 11.6), (0.15, 0.3, 0.7)),
    'Sensor_sonda':     (cilindro_y(133.6, 27.6, 10.9, 0.0, 22.0), (0.2, 0.2, 0.2)),
    # Módulo LED bicolor contra la pared frontal, con el LED en su agujero (x 31,6, z 41,6)
    'LED_PCB':          (caja(24.1, 8.6, 34.0, 39.1, 10.2, 47.5), (0.12, 0.12, 0.12)),
    'LED_5mm':          (cilindro_y(31.6, 41.6, 2.5, 0.0, 8.6), (0.85, 0.2, 0.2)),
    # Módulo buzzer pasivo con el buzzer metido en el agujero de la pared derecha
    # (agujero Ø12,7 en x = 163,2, centro y = 99,6, z = 33,6); el frente queda al ras de la pared
    'Buzzer_PCB':       (caja(153.6, 90.35, 26.1, 155.2, 108.85, 41.1), (0.12, 0.12, 0.12)),
    'Buzzer_cuerpo':    (cilindro_x(99.6, 33.6, 6.0, 155.2, 163.2), (0.1, 0.1, 0.1)),
}

ensamble = cq.Assembly(name='Componentes_sensor_estacionamiento')
for nombre, (forma, color) in piezas.items():
    ensamble.add(forma, name=nombre, color=cq.Color(*color))
ensamble.save('componentes.step')

# Tapa en posición de ensamble: girar 180° en x y subirla sobre los muros (alto 49,6)
tapa = trimesh.load('caja_tapa_amplia.stl')
tapa.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
tapa.apply_translation([0, 0, 49.6])
tapa.export('caja_tapa_ensamble.stl')

# Revisión de interferencias contra la base y la tapa
base = trimesh.load('caja_base_amplia.stl')
print('tapa ensamble bounds', tapa.bounds.round(1).tolist())
for nombre, (forma, _) in piezas.items():
    forma.val().exportStl(f'/tmp/{nombre}.stl', tolerance=0.05)
    m = trimesh.load(f'/tmp/{nombre}.stl')
    v = 0.0
    for c in (base, tapa):
        inter = trimesh.boolean.intersection([m, c], engine='manifold')
        v += inter.volume if not inter.is_empty else 0.0
    print(f'{nombre:16s} interferencia {v:7.2f} mm3')
