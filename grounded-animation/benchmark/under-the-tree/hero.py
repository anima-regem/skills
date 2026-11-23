"""Standalone, unmeasured 1280x720 still for Under the Tree in Blender 5.2.

Run from factory startup: Blender -b --factory-startup --disable-autoexec -P hero.py.
Pass --preview after -- to render a reduced-resolution proof.
"""
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ASSETS = HERE / 'assets'
ENV = ASSETS / 'environment'
PREVIEW = '--preview' in sys.argv
random.seed(71)


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def mesh_object(name, vertices, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def uv_cylinder(mesh, segments, repeats):
    layer = mesh.uv_layers.new(name='Bark UV')
    for polygon in mesh.polygons:
        row, col = divmod(polygon.index, segments)
        for loop, (du, dv) in zip(polygon.loop_indices, ((0, 0), (1, 0), (1, 1), (0, 1))):
            layer.data[loop].uv = ((col+du) / segments * repeats, (row+dv) * .110)


def set_world(scene, camera):
    world = bpy.data.worlds.new('Neutral open-sky ambience')
    scene.world = world
    world.node_tree.nodes.get('Background').inputs['Color'].default_value = (.055,.071,.090,1)
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .45
    # Stage the distant sweep of the supplied panorama at a real depth so it
    # takes the lens blur. Near grass and bark are lit scene geometry.
    distance = 9.0
    half_width = distance * camera.data.sensor_width / camera.data.lens * .512
    half_height = half_width * 720 / 1280
    q = camera.rotation_euler.to_quaternion()
    center = camera.location + q @ Vector((0,0,-distance))
    local = [(-half_width,-half_height),(half_width,-half_height),
             (half_width,half_height),(-half_width,half_height)]
    vertices = [center + q @ Vector((x,y,0)) for x,y in local]
    backdrop = mesh_object('Distant autumn meadow', vertices, [(0,1,2,3)])
    uv = backdrop.data.uv_layers.new(name='Panorama crop')
    for loop, (u,v) in zip(backdrop.data.polygons[0].loop_indices, ((.005,.315),(.295,.315),(.295,.641),(.005,.641))):
        uv.data[loop].uv = (u,v)
    material = bpy.data.materials.new('Open late-afternoon field')
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(str(ENV / 'autumn_meadow_1k.hdr'),check_existing=True)
    emission=nodes.new('ShaderNodeEmission')
    emission.inputs['Strength'].default_value=.78
    output=nodes.new('ShaderNodeOutputMaterial')
    links.new(texture.outputs['Color'],emission.inputs['Color'])
    links.new(emission.outputs[0],output.inputs['Surface'])
    backdrop.data.materials.append(material)


def tree():
    sides, rows = 86, 35
    verts = []
    for k in range(rows):
        z = .94 + .11 * k
        taper = max(.80, 1.09 - (z - 1.40) * .066)
        for j in range(sides):
            angle = 2 * math.pi * j / sides
            ridges = .008 * math.sin(9*angle + .18*z) + .0045 * math.sin(17*angle - .8*z)
            radius = .177*taper + ridges + .008 * math.sin(4*angle + z)
            verts.append((-.200 + .012*(z-1.5) + radius*math.cos(angle),
                          .159 - .018*(z-1.5) + radius*.93*math.sin(angle),z))
    faces = []
    for k in range(rows-1):
        for j in range(sides):
            a = k*sides+j
            b = k*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    obj = mesh_object('Oak trunk at his shoulder', verts, faces)
    uv_cylinder(obj.data, sides, 1.7)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    material = bpy.data.materials.new('Weathered oak bark')
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    surface = nodes.get('Principled BSDF')
    surface.inputs['Roughness'].default_value = .88
    surface.inputs['Specular IOR Level'].default_value = .22
    albedo = nodes.new('ShaderNodeTexImage')
    albedo.image = bpy.data.images.load(str(ENV / 'oak_bark_diffuse.jpg'), check_existing=True)
    normal_tex = nodes.new('ShaderNodeTexImage')
    normal_tex.image = bpy.data.images.load(str(ENV / 'oak_bark_normal.jpg'), check_existing=True)
    normal_tex.image.colorspace_settings.name = 'Non-Color'
    normal = nodes.new('ShaderNodeNormalMap')
    normal.inputs['Strength'].default_value = .9
    links.new(albedo.outputs['Color'], surface.inputs['Base Color'])
    links.new(normal_tex.outputs['Color'], normal.inputs['Color'])
    links.new(normal.outputs['Normal'], surface.inputs['Normal'])
    obj.data.materials.append(material)
    return obj


def grass():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ENV / 'grass' / 'grass_medium_01_1k.gltf'))
    imported = [obj for obj in bpy.data.objects if obj not in before]
    donors = sorted([o for o in imported if 'mid_' in o.name or 'tall_' in o.name], key=lambda o:o.name)
    for o in imported:
        if o not in donors:
            bpy.data.objects.remove(o, do_unlink=True)
    for j in range(36):
        donor = donors[j % len(donors)]
        instance = bpy.data.objects.new('Meadow tuft', donor.data)
        bpy.context.scene.collection.objects.link(instance)
        x = random.uniform(.18, 2.4)
        y = random.uniform(1.04, 3.20)
        z = 1.238 + random.uniform(-.05, .025)
        scale = random.uniform(1.0, 1.8)
        instance.location = (x,y,z)
        instance.scale = (scale,scale,scale)
        instance.rotation_euler.z = random.uniform(0, math.tau)
    for o in donors:
        bpy.data.objects.remove(o, do_unlink=True)


def drifting_leaf(camera, points_at):
    center = Vector(points_at)
    q = camera.rotation_euler.to_quaternion()
    right = q @ Vector((1,0,0))
    up = q @ Vector((0,1,0))
    forward = q @ Vector((0,0,-1))
    length = (right*.44 + up*.88 + forward*.20).normalized()
    across = (-right*.84 + up*.50 - forward*.25).normalized()
    normal = across.cross(length).normalized()
    # A low-curvature silhouette with asymmetrical oak lobes.
    outline = [
        (-.004,-.020),(-.007,-.013),(-.013,-.012),(-.014,-.006),(-.010,-.003),
        (-.018,.001),(-.016,.007),(-.010,.010),(-.013,.015),(-.008,.021),
        (-.003,.022),(0,.027),(.004,.021),(.009,.022),(.012,.017),
        (.009,.012),(.016,.010),(.017,.003),(.010,.000),(.014,-.005),
        (.012,-.010),(.006,-.015),(.003,-.019)
    ]
    verts = [tuple(center + across*x + length*y + normal*(.003 - abs(x)*.2 + 6*y*y)) for x,y in outline]
    verts.append(tuple(center+normal*.003))
    n=len(outline)
    obj=mesh_object('One falling oak leaf',verts,[(n,i,(i+1)%n) for i in range(n)])
    for poly in obj.data.polygons:
        poly.use_smooth=True
    material=bpy.data.materials.new('Copper leaf')
    material.use_nodes=True
    nodes,links=material.node_tree.nodes,material.node_tree.links
    principled=nodes.get('Principled BSDF')
    principled.inputs['Roughness'].default_value=.63
    principled.inputs['Subsurface Weight'].default_value=.06
    principled.inputs['Subsurface Radius'].default_value=(1.0,.45,.12)
    tex=nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value=8.0
    tex.inputs['Detail'].default_value=3.0
    ramp=nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=.20
    ramp.color_ramp.elements[0].color=(.075,.017,.004,1)
    ramp.color_ramp.elements[1].position=.84
    ramp.color_ramp.elements[1].color=(.42,.12,.018,1)
    links.new(tex.outputs['Fac'],ramp.inputs[0])
    links.new(ramp.outputs['Color'],principled.inputs['Base Color'])
    obj.data.materials.append(material)

    vein_mat=bpy.data.materials.new('Amber leaf veins')
    vein_mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.27,.105,.009,1)
    stems=bpy.data.curves.new('Petiole and oak veins','CURVE')
    stems.dimensions='3D'
    stems.bevel_depth=.00010
    stems.bevel_resolution=2
    def vein(coords):
        spline=stems.splines.new('POLY')
        spline.points.add(len(coords)-1)
        for p,(x,y) in zip(spline.points,coords):
            v=center+across*x+length*y+normal*(.0033-abs(x)*.2+6*y*y)
            p.co=(*v,1)
    vein([(0,y) for y in (-.028,-.016,-.004,.008,.020,.026)])
    for side in (-1,1):
        for y,reach in ((-.011,.009),(-.004,.013),(.004,.014),(.010,.009)):
            vein([(0,y),(side*reach*.5,y+.002),(side*reach,y+.004)])
    stems.materials.append(vein_mat)
    detail=bpy.data.objects.new('Fine oak leaf veins',stems)
    bpy.context.scene.collection.objects.link(detail)

def lighting(scene):
    setup = [
        ('Cool skylight',(-.42,-.52,2.18),7.4,.50,(.83,.91,1.0)),
        ('Soft field bounce',(.46,-.48,1.48),2.2,.85,(.97,1.0,.86)),
        ('Low golden edge',(.44,.35,1.84),10.0,.31,(1.0,.73,.45)),
        ('Sky catchlight',(-.04,-.46,1.97),1.4,.21,(.83,.92,1.0)),
        ('Grazing oak bounce',(-.47,-.02,1.94),2.4,.36,(1.0,.81,.58)),
    ]
    for name,pos,watt,diameter,color in setup:
        data=bpy.data.lights.new(name,'AREA')
        data.energy=watt
        data.shape='DISK'
        data.size=diameter
        data.color=color
        data.use_shadow=False
        o=bpy.data.objects.new(name,data)
        scene.collection.objects.link(o)
        o.location=pos
        aim(o,(-.02,-.072,1.62))
    sun=bpy.data.lights.new('Late sun grazing the field','SUN')
    sun.energy=.75
    sun.color=(1,.82,.62)
    sun.angle=.17
    sun.use_shadow=False
    o=bpy.data.objects.new(sun.name,sun)
    scene.collection.objects.link(o)
    o.location=(.4,.30,2.1)
    aim(o,(-.10,.03,1.40))
    # Keep the character under tree shade while the field remains in the sun.
    if hasattr(o,'light_linking'):
        receiver=bpy.data.collections.new('Sun receivers')
        receiver.objects.link(bpy.data.objects['Oak trunk at his shoulder'])
        for turf in [g for g in scene.objects if g.name.startswith('Meadow tuft')]:
            receiver.objects.link(turf)
        o.light_linking.receiver_collection=receiver


scene=bpy.context.scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj,do_unlink=True)
with bpy.data.libraries.load(str(ASSETS/'einar.blend'),link=False) as (_,loaded):
    loaded.collections=['CH-einar']
scene.collection.children.link(loaded.collections[0])
rig=bpy.data.objects['RIG-einar']
rig.pose.bones['FK-Head'].rotation_euler.y=.045
rig.pose.bones['FK-Head'].rotation_euler.x=-.020
rig.pose.bones['Blink.L'].location.y=.0008
rig.pose.bones['Blink.R'].location.y=.0016
rig.pose.bones['ACT-Eyebrow_Inner.L'].location.y=-.0006
rig.pose.bones['ACT-Eyebrow_Inner.R'].location.y=.0026
rig.pose.bones['ACT-Eyebrow_Outer.R'].location.y=.0021
rig.pose.bones['MSTR-TGT-Eyes'].location.x=.13
rig.pose.bones['MSTR-TGT-Eyes'].location.z=.015
rig.pose.bones['MSTR-Jaw'].rotation_euler.x=.024
rig.pose.bones['ACT-Mouth_Corner.L'].location.y=-.0012
rig.pose.bones['ACT-Mouth_Corner.R'].location.y=-.0006

camera=bpy.data.objects.new('Portrait',bpy.data.cameras.new('Portrait'))
scene.collection.objects.link(camera)
camera.location=(-.238,-.802,1.654)
camera.data.lens=68.0
camera.data.dof.use_dof=True
camera.data.dof.aperture_fstop=8.0
focus=Vector((-.002,-.115,1.675))
camera.data.dof.focus_distance=(focus-camera.location).length
aim(camera,(.063,-.058,1.653))
scene.camera=camera
set_world(scene,camera)
for side in ('L','R'):
    bpy.data.objects[f'GEO-eye.cornea.{side}'].hide_render=True
tree()
grass()
drifting_leaf(camera,(.163,-.105,1.692))
lighting(scene)

scene.render.engine='BLENDER_EEVEE'
scene.eevee.use_shadows=False
scene.eevee.taa_render_samples=12 if PREVIEW else 56
scene.render.use_simplify=True
scene.render.simplify_subdivision=2
scene.render.simplify_subdivision_render=2
scene.render.resolution_x=1280
scene.render.resolution_y=720
scene.render.resolution_percentage=50 if PREVIEW else 100
scene.render.hair_type='STRIP'
scene.render.hair_subdiv=0
scene.render.film_transparent=False
scene.view_settings.view_transform='Filmic'
scene.view_settings.look='Medium High Contrast'
scene.view_settings.exposure=-.20
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(HERE/('preview.png' if PREVIEW else 'hero.png'))
bpy.context.view_layer.update()
print('UNMEASURED HERO',scene.render.filepath,flush=True)
bpy.ops.render.render(write_still=True)
