"""Build the riverbank shot with Blender's background Python entry point."""
from math import atan2, cos, pi, sin, tau
from pathlib import Path
from random import Random

import bpy
from mathutils import Quaternion, Vector

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'
rng = Random(203)


def material(name, color, roughness=.78):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return mat


def mesh_object(name, vertices, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def pebble(name, center, scale, mat, detail=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=detail, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler.z = rng.uniform(0, tau)
    obj.data.materials.append(mat)
    return obj


def linear_keys(obj, property_name, start, end):
    for frame, value in ((1, start), (48, end)):
        setattr(obj, property_name, value)
        obj.keyframe_insert(data_path=property_name, frame=frame)
    action = obj.animation_data.action
    for curve in action.layers[0].strips[0].channelbag(obj.animation_data.action_slot).fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'


def near(x):
    return -2.0 + .36 * sin(.39*x + .75) + .095 * sin(1.0*x)


def far(x):
    return 3.2 + .68 * sin(.32*x + .22)


def bank(name, edge, side, height, colors):
    profile = [(-.11, -.22), (.05, .035), (.22, height*.68),
               (.44, height), (1.2, height+.02), (2.8, height+.10),
               (6, height+.33), (15, height+.45)]
    vertices = []
    width = len(profile)
    for i in range(123):
        x = (i-61)*.32
        for j, (offset, z) in enumerate(profile):
            relief = sin(x*.9+j*.83)*.038 + sin(x*.39+j*.52)*.029
            vertices.append((x, edge(x)+side*offset, z+relief))
    faces = []
    for i in range(122):
        for j in range(width-1):
            k = i*width+j
            face = (k, k+width, k+width+1, k+1)
            faces.append(face if side > 0 else face[::-1])
    obj = mesh_object(name, vertices, faces, colors[0])
    for mat in colors[1:]:
        obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        row = poly.index % (width-1)
        poly.material_index = (0, 1, 1, 2, 2, 3, 3)[row]
        poly.use_smooth = True


sand = material('Wet ochre sand', (.24, .152, .081))
clay = material('Terracotta cut bank', (.40, .258, .137))
moss = material('Sage meadow', (.158, .248, .123))
grass = material('Distant sage', (.21, .31, .17))
bank('Near bank', near, -1, .43, [sand, clay, moss, grass])
bank('Far bank', far, 1, .33, [sand, clay, moss, grass])

water = material('Jade water', (.033, .30, .29), .27)
nodes = water.node_tree.nodes
links = water.node_tree.links
coords = nodes.new('ShaderNodeTexCoord')
mapping = nodes.new('ShaderNodeMapping')
mapping.inputs['Scale'].default_value = (.48, 2.7, 1)
links.new(coords.outputs['Object'], mapping.inputs['Vector'])
for frame, offset in ((1, 0), (48, -2.35)):
    mapping.inputs['Location'].default_value.x = offset
    mapping.inputs['Location'].keyframe_insert(data_path='default_value', frame=frame)
animation = water.node_tree.animation_data
for curve in animation.action.layers[0].strips[0].channelbag(animation.action_slot).fcurves:
    for key in curve.keyframe_points:
        key.interpolation = 'LINEAR'
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.5
noise.inputs['Detail'].default_value = 2.2
links.new(mapping.outputs[0], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .16
ramp.color_ramp.elements[0].color = (.012, .15, .17, 1)
ramp.color_ramp.elements[1].position = .86
ramp.color_ramp.elements[1].color = (.065, .39, .37, 1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
shader = nodes.get('Principled BSDF')
links.new(ramp.outputs[0], shader.inputs['Base Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .24
bump.inputs['Distance'].default_value = .046
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs[0], shader.inputs['Normal'])
mesh_object('River surface', [(-20,-3,0), (20,-3,0), (20,5,0), (-20,5,0)], [(0,1,2,3)], water)

glints = [material('Current · '+name, color, .48) for name, color in [
    ('jade', (.072,.39,.35)), ('mint', (.17,.54,.46)),
    ('light', (.40,.69,.55)), ('foam', (.65,.82,.68))]]


def flash(name, x, y, length, width, mat, speed, z=.016, bend=.028):
    vertices = []
    for i in range(13):
        t = i/12
        taper = max(.012, sin(pi*t))**.82 * (1.38-.76*t)
        center = bend*sin(pi*t)
        vertices += [(length*t, center-width*taper, z), (length*t, center+width*taper, z)]
    obj = mesh_object(name, vertices, [(2*i,2*i+2,2*i+3,2*i+1) for i in range(12)], mat)
    linear_keys(obj, 'location', (x,y,0), (x+speed,y,0))
    return obj


for i in range(95):
    y = rng.uniform(-1.54, 2.43)
    speed = 3.2 + 2.25*sin(pi*(y+1.76)/4.8)
    flash('Traveling surface glint', rng.uniform(-15, 11), y,
          rng.uniform(.17, 1.27), rng.uniform(.008,.037),
          rng.choices(glints, [6,7,3,1])[0], speed, bend=rng.uniform(-.055,.055))

rock_materials = [material('River stone · '+name, color) for name, color in
                  [('slate', (.12,.19,.18)), ('lichen', (.246,.301,.21)), ('chalk', (.36,.37,.26))]]
for edge, side in ((near,-1),(far,1)):
    for i in range(43):
        x = rng.uniform(-13, 13)
        offset = rng.uniform(.02,.63)
        radius = rng.uniform(.045,.22)
        pebble('Shingle', (x,edge(x)+side*offset,.04+.4*offset),
               (radius*1.35,radius,radius*.62), rng.choice(rock_materials), 2)

for x, y, size in ((2.6,.83,.42), (3.13,.95,.23), (-5.48,1.72,.29)):
    pebble('Current boulder', (x,y,.05), (size*1.38,size,size*.7), rock_materials[0], 2)
    for side in (-1,1):
        flash('Water parting around stone', x-size*.98, y+side*size*.84,
              size*4.5,.019,glints[2],0,bend=side*size*.42)
        for j in range(3):
            flash('Broken wake', x+size*(1.43+j*.84), y+side*(size*.95+j*.035),
                  size*.57,.015,glints[1+j%2],0,z=.021+j*.001,bend=side*.031)

stems = [material('Reed · '+name, color) for name,color in [
    ('olive', (.23,.30,.087)), ('straw', (.57,.415,.15)), ('green', (.086,.18,.081))]]
for edge, side, height in ((near,-1,.43),(far,1,.33)):
    vertices, faces, indices = [], [], []
    for k in range(56):
        x = rng.uniform(-14,14)
        offset = rng.uniform(.27,1.03)
        if side < 0 and -3.85 < x < -1.85:
            continue
        y = edge(x)+side*offset
        for j in range(rng.randrange(4,10)):
            px, py = x+rng.uniform(-.15,.15), y+rng.uniform(-.13,.13)
            z = height-.094 if offset<.44 else height-.018
            h = rng.uniform(.15,.56)
            lean_x, lean_y = rng.uniform(-.26,.26), rng.uniform(-.22,.22)
            yaw = rng.uniform(0,tau)
            w = rng.uniform(.013,.035)
            k0 = len(vertices)
            for t, width in ((0,.47),(.42,1),(.78,.63),(1,.012)):
                for sign in (-1,1):
                    vertices.append((px+lean_x*t*t+sign*w*width*cos(yaw),
                                     py+lean_y*t*t+sign*w*width*sin(yaw), z+h*t))
            for n in range(0,6,2):
                faces.append((k0+n,k0+n+1,k0+n+3,k0+n+2))
            indices.extend([rng.randrange(3)]*3)
    obj = mesh_object('Riverbank grasses', vertices, faces, stems[0])
    for mat in stems[1:]:
        obj.data.materials.append(mat)
    for poly, index in zip(obj.data.polygons, indices):
        poly.material_index = index

leaf_mat = material('Copper leaf', (.81,.275,.043), .53)
leaf_vein = material('Leaf midrib', (.99,.49,.122))
leaf = mesh_object('Drifting copper leaf',
                   [(-.23,0,.018),(-.09,-.083,.018),(.10,-.061,.014),(.23,.012,.026),
                    (.076,.091,.032),(-.093,.067,.03),(0,0,.042)],
                   [(i,(i+1)%6,6) for i in range(6)],leaf_mat)
vein = mesh_object('Leaf midrib', [(-.18,0,.023),(0,-.009,.045),(.19,.01,.03),(0,.009,.045)],
                   [(0,1,2,3)],leaf_vein)
vein.parent = leaf
linear_keys(leaf,'location',(-4.1,-.91,.013),(.74,-.83,.013))
for frame, angle in ((1,-.23),(13,.13),(28,-.15),(48,.37)):
    leaf.rotation_euler.z = angle
    leaf.keyframe_insert(data_path='rotation_euler',frame=frame)

# Adapt the supplied skinned idle and direct its head toward the drifting leaf.
bpy.ops.import_scene.gltf(filepath=str(Path(__file__).resolve().parent / 'assets' / 'watcher.glb'))
imported = list(bpy.context.selected_objects)
root = next(o for o in imported if o.parent is None)
rig = next(o for o in imported if o.type == 'ARMATURE')
body = next(o for o in imported if o.name == 'SuperHero_Male')
root.name = 'Watcher'
root.animation_data_clear()
root.rotation_mode = 'XYZ'
root.location = (-2.75, near(-2.75)-.78, .43)
root.rotation_euler.z = 2.63
root.scale = (1.18,)*3
rig_action = rig.animation_data.action
for curve in rig_action.layers[0].strips[0].channelbag(rig.animation_data.action_slot).fcurves:
    for key in curve.keyframe_points:
        key.co.x = 1 + key.co.x * (47/30)
        key.handle_left.x = 1 + key.handle_left.x * (47/30)
        key.handle_right.x = 1 + key.handle_right.x * (47/30)
    curve.update()

outfit = [
    material('Ochre canvas jacket', (.72,.23,.045)),
    material('Indigo trousers', (.036,.069,.088)),
    material('Dark leather boots', (.045,.036,.026)),
    material('Warm skin', (.49,.234,.129), .62),
    material('Knit collar', (.105,.057,.032)),
]
body.data.materials.clear()
for mat in outfit:
    body.data.materials.append(mat)
group_names = [g.name.lower() for g in body.vertex_groups]
for poly in body.data.polygons:
    z = sum(body.data.vertices[i].co.z for i in poly.vertices)/len(poly.vertices)
    influences = {}
    for i in poly.vertices:
        for group in body.data.vertices[i].groups:
            name = group_names[group.group]
            influences[name] = influences.get(name,0) + group.weight
    bone = max(influences, key=influences.get, default='')
    if bone in ('head','head_leaf') or bone.startswith(('hand','thumb','index','middle','ring','pinky')):
        index = 3
    elif bone.startswith('neck'):
        index = 4 if z < 1.54 else 3
    elif z < .122:
        index = 2
    elif bone.startswith(('calf','thigh','foot','ball')) or (bone=='pelvis' and z < .92):
        index = 1
    else:
        index = 0
    poly.material_index = index

for obj in imported:
    if obj.name in ('Eyes','Eyebrows'):
        obj.data.materials[0] = material(obj.name, (.044,.028,.018))

# Sample the idle before writing any of the new head keys.
head = rig.pose.bones['Head']
scene.frame_set(1)
cap_material = material('Dark teal knit', (.027,.083,.086))
cuff_material = material('Folded knit cuff', (.047,.126,.123))
cap_profile = [(1,1.681),(1.035,1.693),(1.025,1.715),(.96,1.723),
               (.91,1.759),(.67,1.797),(.31,1.815),(.02,1.822)]
cap_vertices = [(radius*.106*cos(tau*i/32), -.148+radius*.109*sin(tau*i/32), z)
                for radius,z in cap_profile for i in range(32)]
cap_faces = [(r*32+i,r*32+(i+1)%32,(r+1)*32+(i+1)%32,(r+1)*32+i)
             for r in range(len(cap_profile)-1) for i in range(32)]
cap_faces.append(tuple((len(cap_profile)-1)*32+i for i in range(32)))
cap = mesh_object('Knitted river cap',cap_vertices,cap_faces,cap_material)
cap.data.materials.append(cuff_material)
for poly in cap.data.polygons:
    poly.material_index = int(poly.index < 96)
    poly.use_smooth = True
cap.parent = rig
cap.parent_type = 'BONE'
cap.parent_bone = head.name
bpy.context.view_layer.update()
cap.matrix_world = rig.matrix_world.copy()

poses = []
for frame in (1, 6, 12, 18, 24, 30, 36, 42, 48):
    scene.frame_set(frame)
    origin = rig.matrix_world @ head.head
    target = leaf.matrix_world.translation.copy()
    target.z = .09
    direction = target-origin
    yaw = max(-.86,min(.94, atan2(direction.x,direction.y)- (pi-root.rotation_euler.z)))
    pitch = atan2(-direction.z, max(1.0,direction.xy.length))*.74
    adjustment = Quaternion((0,0,1), -yaw) @ Quaternion((1,0,0),pitch)
    desired = head.matrix.copy()
    desired_rotation = adjustment @ desired.to_quaternion()
    desired = desired_rotation.to_matrix().to_4x4()
    desired.translation = head.head
    head.matrix = desired
    poses.append((frame,head.rotation_quaternion.copy()))
# Replace the source head rotation samples so the directed gaze is continuous.
for curve in list(rig_action.layers[0].strips[0].channelbag(rig.animation_data.action_slot).fcurves):
    if curve.data_path == head.path_from_id('rotation_quaternion'):
        rig_action.layers[0].strips[0].channelbag(rig.animation_data.action_slot).fcurves.remove(curve)
for frame, quat in poses:
    head.rotation_quaternion = quat
    head.keyframe_insert(data_path='rotation_quaternion',frame=frame)

scene.frame_set(1)

shrub_colors = [
    material('Willow foliage', (.112,.211,.095)),
    material('Sunlit willow foliage', (.186,.287,.105)),
    material('Shaded willow foliage', (.074,.144,.079)),
]
for x, offset, size in ((-8,1.8,.77),(-6.7,2.2,.65),(-.3,2.0,.57),
                        (.86,2.5,.73),(5.6,1.4,.65),(6.42,1.9,.88),(8,2.7,1.13)):
    y = far(x)+offset
    for j in range(6):
        pebble('Low willow', (x+rng.uniform(-.63,.63)*size,
                             y+rng.uniform(-.52,.52)*size,.4+rng.uniform(.17,.6)*size),
               (size*rng.uniform(.42,.72),size*.62,size*rng.uniform(.45,.75)),
               rng.choice(shrub_colors), 2)


def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()


bpy.ops.object.camera_add(location=(4.9,-10.1,6.2))
camera = bpy.context.object
camera.name = 'Riverbank camera'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 10.85
aim(camera, (-.35,.14,.49))
scene.camera = camera

bpy.ops.object.light_add(type='SUN',location=(-4,-3,9))
sun = bpy.context.object
sun.name = 'Warm afternoon sun'
sun.data.energy = 2.35
sun.data.color = (1,.84,.66)
sun.data.angle = .16
aim(sun,(1,1,0))

world = scene.world
background = world.node_tree.nodes['Background']
background.inputs['Color'].default_value = (.69,.81,1,1)
background.inputs['Strength'].default_value = .36

scene.frame_set(1)
