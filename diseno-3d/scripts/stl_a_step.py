"""Convierte los STL de la caja en sólidos BRep (STEP) uniendo los triángulos coplanares en caras planas."""
import sys
import trimesh
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeSolid
from OCP.gp import gp_Pnt
from OCP.TopoDS import TopoDS
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.ShapeFix import ShapeFix_Solid
import cadquery as cq

def convertir(stl, step, nombre):
    m = trimesh.load(stl)
    sew = BRepBuilderAPI_Sewing(1e-4)
    for f in m.faces:
        a, b, c = (gp_Pnt(*map(float, m.vertices[i])) for i in f)
        poly = BRepBuilderAPI_MakePolygon(a, b, c, True)
        face = BRepBuilderAPI_MakeFace(poly.Wire(), True)
        if face.IsDone():
            sew.Add(face.Face())
    sew.Perform()
    shell = TopoDS.Shell_s(sew.SewedShape())
    solid = BRepBuilderAPI_MakeSolid(shell).Solid()
    fix = ShapeFix_Solid(solid); fix.Perform(); solid = fix.Solid()
    uni = ShapeUpgrade_UnifySameDomain(solid, True, True, True); uni.Build()
    forma = cq.Shape.cast(uni.Shape())
    print(nombre, 'caras', len(forma.Faces()), 'valido', forma.isValid(), 'volumen', round(forma.Volume(), 1), 'stl', round(m.volume, 1))
    a = cq.Assembly(name=nombre + '_ensamble'); a.add(forma, name=nombre, color=cq.Color(0.35, 0.6, 0.35))
    a.save(step)

convertir('caja_base_amplia.stl', 'caja_base_amplia.step', 'Caja_base')
convertir('caja_tapa_ensamble.stl', 'caja_tapa_ensamble.step', 'Caja_tapa')
