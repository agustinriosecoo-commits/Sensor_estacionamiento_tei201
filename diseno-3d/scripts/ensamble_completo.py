"""Une la caja (base y tapa ya convertidas a sólido) y los componentes en un solo STEP para Fusion 360."""
import cadquery as cq
a = cq.Assembly(name='Sensor_estacionamiento')
for archivo, nombre, color in [('caja_base_amplia.step', 'Caja_base', (0.35, 0.65, 0.35)),
                               ('caja_tapa_ensamble.step', 'Caja_tapa', (0.35, 0.65, 0.35))]:
    a.add(cq.importers.importStep(archivo), name=nombre, color=cq.Color(*color))
a.add(cq.Assembly.load('componentes.step') if hasattr(cq.Assembly, 'load') else cq.importers.importStep('componentes.step'), name='Componentes')
a.save('ensamble_completo.step')
