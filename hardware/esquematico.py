"""Esquemático del sensor de ocupación de estacionamiento (TEI201, Grupo 10), versión 9.
Genera esquematico.pdf y esquematico.png con matplotlib.
Las alimentaciones se dibujan con símbolos de red (3V3, GND): todas las redes con el mismo
nombre están unidas (en el prototipo, por los rieles de la breadboard).
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(16, 9.5))
ax.set_aspect('equal')
ax.axis('off')
LW = 1.8


def caja(x0, y0, x1, y1, titulo, sub='', arriba=True):
    ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=2.2))
    cx = (x0 + x1) / 2
    if arriba:   # título sobre la caja, para no tapar los nombres de los pines
        ax.text(cx, y1 + 0.2, sub, ha='center', va='bottom', fontsize=9, color='#333')
        ax.text(cx, y1 + 0.2 + 0.32 * (sub.count('\n') + 1) + 0.12, titulo, ha='center', va='bottom', fontsize=12, weight='bold')
    else:
        ax.text(cx, (y0 + y1) / 2 + 0.25, titulo, ha='center', va='center', fontsize=12, weight='bold')
        ax.text(cx, (y0 + y1) / 2 - 0.45, sub, ha='center', va='center', fontsize=9.5, color='#333')


def pin(x, y, nombre, lado, externo=''):
    """Punto de conexión en el borde de una caja. lado = 'izq', 'der' o 'arr' (dónde está el pin)."""
    ax.plot(x, y, 'o', color='k', ms=5, zorder=5)
    if lado == 'izq':
        ax.text(x + 0.15, y, nombre, ha='left', va='center', fontsize=10)
        if externo: ax.text(x - 0.1, y + 0.18, externo, ha='right', va='bottom', fontsize=8, color='#555')
    elif lado == 'der':
        ax.text(x - 0.15, y, nombre, ha='right', va='center', fontsize=10)
        if externo: ax.text(x + 0.1, y + 0.18, externo, ha='left', va='bottom', fontsize=8, color='#555')
    else:
        ax.text(x, y - 0.2, nombre, ha='center', va='top', fontsize=10)


def cable(*pts, etiqueta=None, pos=0.5):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color='k', lw=LW)
    if etiqueta:
        (xa, ya), (xb, yb) = pts[0], pts[-1]
        ax.text(xa + (xb - xa) * pos, ya + 0.15, etiqueta, ha='center', va='bottom', fontsize=9.5, color='#1f4e9e')


def resistencia(x0, x1, y, nombre, valor):
    """Resistencia horizontal entre x0 y x1 (zigzag en el tramo central)."""
    largo = x1 - x0
    a, b = x0 + largo * 0.25, x1 - largo * 0.25
    n = 6
    xs = np.linspace(a, b, 2 * n + 1)
    ys = [y + (0.18 if i % 2 else -0.18) if 0 < i < 2 * n else y for i in range(2 * n + 1)]
    ax.plot([x0, a], [y, y], 'k', lw=LW)
    ax.plot(xs, ys, 'k', lw=LW)
    ax.plot([b, x1], [y, y], 'k', lw=LW)
    ax.text((x0 + x1) / 2, y + 0.3, f'{nombre}  {valor}', ha='center', va='bottom', fontsize=9.5, weight='bold')


def vcc(x, y, nombre='3V3', alto=0.55):
    ax.plot([x, x], [y, y + alto], 'k', lw=LW)
    ax.plot([x - 0.25, x + 0.25], [y + alto, y + alto], 'k', lw=2.4)
    ax.text(x, y + alto + 0.1, nombre, ha='center', va='bottom', fontsize=9.5, color='#b3362c', weight='bold')


def tierra(x, y, alto=0.5):
    ax.plot([x, x], [y, y - alto], 'k', lw=LW)
    for i, w in enumerate([0.3, 0.2, 0.1]):
        yy = y - alto - i * 0.1
        ax.plot([x - w, x + w], [yy, yy], 'k', lw=LW)


# ---------------- ESP32 ----------------
caja(0, 0, 4, 7.2, 'ESP32 DevKit', 'WROOM-32', arriba=False)
pin(0, 6, 'D5', 'izq', 'GPIO5');   pin(0, 5, 'D18', 'izq', 'GPIO18')
pin(0, 2, '3V3', 'izq');           pin(0, 1, 'GND', 'izq')
pin(4, 6, 'D25', 'der', 'GPIO25'); pin(4, 5, 'D26', 'der', 'GPIO26'); pin(4, 3, 'D27', 'der', 'GPIO27')
pin(2, 7.2, 'VIN', 'arr')
vcc(2, 7.2, 'USB 5 V', alto=0.7)
cable((0, 2), (-0.8, 2)); vcc(-0.8, 2)
cable((0, 1), (-0.8, 1)); tierra(-0.8, 1)

# ---------------- Sensor ----------------
caja(-9.5, 2.5, -6, 6.6, 'Sensor ultrasónico', 'SR04M-2, modo 1 (alimentado a 3,3 V)')
pin(-6, 6, 'RX (Trig)', 'der'); pin(-6, 5, 'TX (Echo)', 'der')
pin(-6, 4, 'VCC', 'der');       pin(-6, 3, 'GND', 'der')
cable((-6, 6), (0, 6), etiqueta='Trig (disparo)')
cable((-6, 5), (-4.6, 5)); resistencia(-4.6, -1.8, 5, 'R3', '1 kΩ'); cable((-1.8, 5), (0, 5))
ax.text(-3.2, 4.55, 'Echo (eco)', ha='center', va='top', fontsize=9.5, color='#1f4e9e')
cable((-6, 4), (-5.2, 4)); vcc(-5.2, 4)
cable((-6, 3), (-5.2, 3)); tierra(-5.2, 3)
# sonda
ax.add_patch(plt.Circle((-10.6, 4.55), 0.45, fill=False, lw=2))
ax.plot([-10.15, -9.5], [4.55, 4.55], 'k', lw=LW)
ax.text(-10.6, 3.85, 'Sonda\nimpermeable', ha='center', va='top', fontsize=8.5)

# ---------------- LED bicolor ----------------
caja(9, 4.0, 12.6, 6.5, 'LED bicolor', 'módulo, cátodo común')
pin(9, 6, 'S (verde)', 'izq'); pin(9, 5, 'Medio (rojo)', 'izq'); pin(9, 4.3, '−', 'izq')
cable((4, 6), (5.3, 6)); resistencia(5.3, 7.9, 6, 'R1', '220 Ω'); cable((7.9, 6), (9, 6))
cable((4, 5), (5.3, 5)); resistencia(5.3, 7.9, 5, 'R2', '220 Ω'); cable((7.9, 5), (9, 5))
cable((9, 4.3), (8.4, 4.3)); tierra(8.4, 4.3, alto=0.35)

# ---------------- Buzzer pasivo ----------------
caja(9, -0.5, 12.6, 2.6, 'Buzzer pasivo', 'módulo, tono 2 kHz')
pin(9, 2.0, 'S', 'izq'); pin(9, 1.0, 'Medio (+)', 'izq'); pin(9, 0.0, '−', 'izq')
cable((4, 3), (6.6, 3), (6.6, 2.0), (9, 2.0))
ax.text(7.8, 2.15, 'PWM (tone)', ha='center', va='bottom', fontsize=9.5, color='#1f4e9e')
cable((9, 1.0), (8.0, 1.0)); vcc(8.0, 1.0, alto=0.4)
cable((9, 0.0), (8.0, 0.0)); tierra(8.0, 0.0, alto=0.35)

# ---------------- Títulos y notas ----------------
ax.text(-11.2, 9.3, 'Sensor de ocupación de estacionamiento · Grupo 10 · TEI201', fontsize=16, weight='bold')
ax.text(-11.2, 8.75, 'Esquemático v9 (16-11-2026). Las redes con el mismo nombre (3V3, GND) están unidas por los rieles de la breadboard.',
        fontsize=10, color='#333')
notas = ('Notas de diseño\n'
         '• El sensor se alimenta a 3,3 V (rango 3 a 5,5 V): así Trig y Echo quedan al nivel lógico del ESP32. Costo: alcance máx. de ~4,5 m baja a ~3 m.\n'
         '• R3 (1 kΩ) en serie en Echo limita la corriente hacia GPIO18 ante un pico de tensión.\n'
         '• R1 y R2 (220 Ω) limitan la corriente de cada color del LED: (3,3 V − ~2 V) / 220 Ω ≈ 6 mA, bajo el máximo de un GPIO.\n'
         '• El buzzer es pasivo: suena solo con una señal oscilante (tone(), 2 kHz) en S.\n'
         '• El ESP32 se alimenta por USB (5 V); su regulador interno entrega los 3,3 V del riel.')
ax.text(-11.2, -0.6, notas, fontsize=9.5, va='top', linespacing=1.5,
        bbox=dict(boxstyle='round,pad=0.5', fc='#f5f5f5', ec='#bbb'))

ax.set_xlim(-11.5, 13.2)
ax.set_ylim(-3.6, 9.8)
fig.savefig('/home/claude/hardware/esquematico.pdf', bbox_inches='tight')
fig.savefig('/home/claude/hardware/esquematico.png', dpi=150, bbox_inches='tight')
print('ok')
