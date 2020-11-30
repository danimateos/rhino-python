import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
from Rhino.Geometry import Point3d, Vector3d, Ellipse, Curve
import math
import random
import System

def single_curve(scale, n_intermediate=3):
    
    zs = [0]
    ys = [0]
    
    for _ in range(n_intermediate):
        zs.append(scale * random.uniform(0, 1))
        ys.append(random.normalvariate(.5, .2) * scale)
    
    zs.sort()
    zs.append(scale)
    ys.append(0)
    xs = [0] * (n_intermediate + 2)
    
    points = [ Rhino.Geometry.Point3d(x,y,z) for x, y, z in zip(xs, ys, zs) ]
    
    return Curve.CreateInterpolatedCurve(points, degree=3)
    

def treetop(scale = 10, **kwargs):
    
    curves = []
    for step in range(4):
        angle = step * math.pi/2
        
        curve = single_curve(scale)
        curve.Rotate(angle, Vector3d(0,0,1), Point3d(0,0,0))
        curves.append(curve)
    
    result = Rhino.Geometry.Brep.CreateFromLoft(curves, Point3d.Unset, Point3d.Unset, Rhino.Geometry.LoftType.Loose, closed=True)
 
    # TODO: material: Paint, (100, 200, 100), matte
    return result # For some reason, it returns an array
    
    
def ellipse(scale = 10, x=0, y=0, z=0):
    base_half_length = scale * random.normalvariate(0.1, .02)
    base_half_width =  scale * random.normalvariate(0.1, .02) 
    
    return Rhino.Geometry.Ellipse(Point3d(x,y,z), Point3d(x + base_half_length, y, z), Point3d(x, y + base_half_width, z))

def jitter(n):
    return n * random.normalvariate(1, .2)

def trunk(scale = 10, n_intermediate = 1, **kwargs):
    
    ellipses = [ellipse(scale)]
    
    for i in range(n_intermediate):
        
        x = jitter(scale/2) - scale / 2
        y = jitter(scale/2) - scale / 2
        z = scale * (i + 1) / (n_intermediate + 1)
        
        this_one = ellipse(scale / 2, x, y, z)
        ellipses.append(this_one)
        
    ellipses.append(ellipse(scale, z = scale))
    
    curves = []
    
    for e in ellipses:
        
        curve = e.ToNurbsCurve()
        curve.Rotate(random.uniform(0, 1) * 2 * math.pi, Vector3d(0,0,1), Point3d(0,0,0))
        #sc.doc.Objects.AddCurve(curve)
        curves.append(curve)
        
    # Normal Loft returns a lot funkier trunks
    result = Rhino.Geometry.Brep.CreateFromLoft(curves, Point3d.Unset, Point3d.Unset, Rhino.Geometry.LoftType.Loose, closed=False)
    result = result[0].CapPlanarHoles(1e-2)
    
    return [result]
 
def tree(scale = 10, **kwargs):
    
    top = treetop(scale, **kwargs)[0]
    tr = trunk(scale, **kwargs)[0]
    
    center_top = Rhino.Geometry.AreaMassProperties.Compute(top).Centroid
    apex_trunk = tr.ClosestPoint(Point3d(0,0, 2*scale))
    
    
    top.Translate(apex_trunk - center_top)
    
    # TODO: align to center of mass
    
    return [tr, top]
    
def rendermaterial(name):
    for rendermaterial in sc.doc.RenderMaterials.GetEnumerator():
        if rendermaterial.Name == name:
            return rendermaterial


def many(scale = 10, side = 5, **kwargs):
    """temp function for playing around
    """
    attributes = Rhino.DocObjects.ObjectAttributes()
    attributes.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject
    
    for x in range(-scale * side, scale * side, 2 * scale):
        for y in range(-scale * side, scale * side, 2 * scale):
            ids = []
            for ix, each in enumerate(tree(scale, **kwargs)):
                
                each.Translate(x, y, 0)

                this_id = sc.doc.Objects.AddBrep(each, attributes)
                obj = rs.coercerhinoobject(this_id)
                obj.RenderMaterial = rendermaterial('bark') if ix == 0 else rendermaterial('leaves')
                obj.CommitChanges()
                
                ids.append(this_id)
            
                
            group_id = sc.doc.Groups.Add(ids)
            
    sc.doc.Views.Redraw()
    

    
def add_materials():
    
    if sc.doc.RenderMaterials.Count > 0:
        return list(sc.doc.RenderMaterials.GetEnumerator())
    
    leaves = Rhino.DocObjects.Material()
    light_green = System.Drawing.Color.FromArgb(255, 100, 200, 100)
    leaves.DiffuseColor = light_green
    leaves.Name = 'leaves'
    render_leaves = Rhino.Render.RenderMaterial.CreateBasicMaterial(leaves)
    sc.doc.RenderMaterials.Add(render_leaves)
    
    
    bark = Rhino.DocObjects.Material()
    light_brown = System.Drawing.Color.FromArgb(255, 200, 100, 30)
    bark.DiffuseColor = light_brown
    bark.Name = 'bark'
    render_bark = Rhino.Render.RenderMaterial.CreateBasicMaterial(bark)
    sc.doc.RenderMaterials.Add(render_bark)

    # from https://github.com/mcneel/rhino-developer-samples/blob/6/rhinopython/SampleAddRenderMaterials.py
    
    
    return render_leaves, render_bark
    
if __name__ == "__main__":
    
    
    leaves, bark = add_materials()
    many(side = 5)
           
    
    sc.doc.Views.Redraw()