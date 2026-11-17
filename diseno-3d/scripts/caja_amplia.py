"""Caja amplia (TEI201, Grupo 10): agranda la caja original sin escalarla.

Método: se "estira" el modelo en planos donde la sección es constante (solo pared lisa y piso),
moviendo todo lo que está más allá del plano. Así las paredes siguen de 1,6 mm y los agujeros
(sensor, LED, tornillos de la tapa) conservan su forma y tamaño.
Después se agregan la cuna del ESP32 (dado vuelta) y la ranura USB-C.
Uso: python3 caja_amplia.py base_original.stl tapa_original.stl base_salida.stl tapa_salida.stl
"""
import sys
import numpy as np
import trimesh
from shapely.geometry import box as sbox

# ---------- Cuánto se agranda (mm) ----------
DX = 40.0   # largo  (x): 123,2 -> 163,2 mm exterior
DY = 30.0   # ancho  (y):  89,2 -> 119,2 mm exterior (sin contar orejas ni visera)
DZ = 10.0   # alto   (z):  39,6 ->  49,6 mm
# Planos de estiramiento: zonas donde la caja original es solo pared lisa
PLANO_X = 68.0      # entre la cuna del ESP32 (x < 59,4) y la visera del sensor (x > 76)
PLANO_Y_BASE = 52.0 # entre la cuna (y < 42,3) y el agujero de la pared derecha (y > 64)
PLANO_Y_TAPA = -52.0
PLANO_Z = 4.0       # sobre el piso (1,6) y bajo el agujero del sensor (z > 6,4)

PARED = PISO = 1.6

# ---------- ESP32 y cuna ----------
LARGO_PLACA, ANCHO_PLACA = 55.0, 28.0   # ANCHO supuesto: medir
HOLGURA, HOLGURA_LARGO = 0.6, 0.8
CENTRO_Y = 26.0
Z_REPISA = 7.5
REPISA, RIEL, Z_RIEL, TOPE = 1.2, 2.0, 11.0, 2.0
# ---------- Ranura USB-C ----------
CENTRO_Z = Z_REPISA - 3.2/2
ANCHO_RANURA, ALTO_RANURA, RADIO = 13.0, 8.0, 2.0


def estirar(m, eje, plano, d):
    """Mueve d mm, a lo largo de 'eje', todos los vértices que están más allá del plano."""
    v = m.vertices.copy()
    if d >= 0:
        v[v[:, eje] > plano, eje] += d
    else:
        v[v[:, eje] < plano, eje] += d
    return trimesh.Trimesh(v, m.faces.copy(), process=True)


base = trimesh.load(sys.argv[1])
tapa = trimesh.load(sys.argv[2])

# 1) Tapar el hueco grande de la pared izquierda y el segundo agujero de LED (antes de estirar)
relleno = trimesh.creation.box(bounds=[[0.0, 12.9, 4.4], [PARED, 26.3, 26.8]])
tapon = trimesh.creation.cylinder(radius=3.0, height=PARED, sections=48)
tapon.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0]))
tapon.apply_translation([43.59, PARED/2, 31.59])
base = trimesh.boolean.union([base, relleno, tapon], engine='manifold')

# 2) Estirar la base en x, y, z y la tapa en x, y
base = estirar(base, 0, PLANO_X, DX)
base = estirar(base, 1, PLANO_Y_BASE, DY)
base = estirar(base, 2, PLANO_Z, DZ)
tapa = estirar(tapa, 0, PLANO_X, DX)
tapa = estirar(tapa, 1, PLANO_Y_TAPA, -DY)

# 3) Cuna del ESP32 dado vuelta
x0 = PARED
x1 = PARED + LARGO_PLACA + HOLGURA_LARGO
ya_in, yb_in = CENTRO_Y - (ANCHO_PLACA + HOLGURA)/2, CENTRO_Y + (ANCHO_PLACA + HOLGURA)/2
piezas = [base]
for y_in, s in ((ya_in, -1), (yb_in, 1)):
    a, b = sorted([y_in, y_in + s*RIEL]);   piezas.append(trimesh.creation.box(bounds=[[x0, a, PISO-0.2], [x1+TOPE, b, Z_RIEL]]))
    a, b = sorted([y_in, y_in - s*REPISA]); piezas.append(trimesh.creation.box(bounds=[[x0, a, PISO-0.2], [x1, b, Z_REPISA]]))
piezas.append(trimesh.creation.box(bounds=[[x1, ya_in-RIEL, PISO-0.2], [x1+TOPE, yb_in+RIEL, Z_RIEL]]))
base = trimesh.boolean.union(piezas, engine='manifold')

# 4) Ranura USB-C frente al conector
perfil = sbox(CENTRO_Y-ANCHO_RANURA/2+RADIO, CENTRO_Z-ALTO_RANURA/2+RADIO,
              CENTRO_Y+ANCHO_RANURA/2-RADIO, CENTRO_Z+ALTO_RANURA/2-RADIO).buffer(RADIO, resolution=16)
corte = trimesh.creation.extrude_polygon(perfil, height=PARED+2.0)
corte.apply_transform(np.array([[0, 0, 1, -1.0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]]))
base = trimesh.boolean.difference([base, corte], engine='manifold')

base.export(sys.argv[3]); tapa.export(sys.argv[4])
for nombre, m in (('base', base), ('tapa', tapa)):
    print(nombre, 'watertight', m.is_watertight, 'bounds', m.bounds.round(1).tolist(), 'vol', round(m.volume, 1))
