"""Build a four-second riverside vignette in Blender 5.2."""
import math
from math import cos, pi, sin
import random
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector


rng = random.Random(85)
scene = bpy.context.scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.52, .65, .74, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .34


def material(name, color, roughness=.75, emission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Emission Color'].default_value = (*color, 1)
    shader.inputs['Emission Strength'].default_value = emission
    return mat


def mesh(name, vertices, faces, mats, indices=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    for mat in mats:
        data.materials.append(mat)
    if indices is not None:
        for poly, index in zip(data.polygons, indices):
            poly.material_index = index
    return obj


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def lit(name, kind, location, power, color, target, size):
    data = bpy.data.lights.new(name, kind)
    data.energy, data.color = power, color
    if kind == 'AREA':
        data.shape, data.size = 'DISK', size
    else:
        data.angle = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)


camera = bpy.data.objects.new('Riverbank composition', bpy.data.cameras.new('Orthographic camera'))
scene.collection.objects.link(camera)
camera.location = (5.6, -11.5, 6.6)
aim(camera, (-.30, -.46, .44))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 9.8
scene.camera = camera
lit('Late afternoon sun', 'SUN', (-5, -3, 7), 2.05, (1, .83, .64), (0, 0, 0), .16)
lit('Cool skylight', 'AREA', (0, 4, 8), 750, (.66, .83, 1), (0, 0, 0), 9)
lit('Soft foreground bounce', 'AREA', (1, -7, 5), 320, (1, .93, .80), (0, 0, 0), 8)

# The channel is about four meters wide. Positive X is downstream.
def center(x):
    return .44*sin(.41*x+.2) + .10*sin(.83*x+1)


def edge(x, side):
    return center(x) + side*(2.03 + .14*cos(.63*x + side))


def flow(d):
    # Stylized surface speed in m/s. USGS WRI 81-71 describes the bank drag.
    return .40 + 1.09*sin(pi*d)**.78


def water_y(x, d):
    return edge(x, -1)*(1-d) + edge(x, 1)*d


def animate(obj, frames, prop):
    for frame, value in frames:
        setattr(obj, prop, value)
        obj.keyframe_insert(data_path=prop, frame=frame)
    action = obj.animation_data.action
    for curve in action.layers[0].strips[0].channelbag(obj.animation_data.action_slot).fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'


def mottle(mat, dark, light, scale):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = 2.2
    links.new(nodes.new('ShaderNodeTexCoord').outputs['Object'], noise.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .24
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = .78
    ramp.color_ramp.elements[1].color = (*light, 1)
    links.new(noise.outputs['Fac'], ramp.inputs[0])
    links.new(ramp.outputs[0], nodes.get('Principled BSDF').inputs['Base Color'])


silt = material('Water-darkened silt', (.28, .17, .084))
sand = material('Warm exposed sand', (.54, .39, .20))
meadow = material('Dry sage meadow', (.34, .36, .16))
mottle(silt, (.19,.13,.068), (.36,.24,.105), 5.5)
mottle(sand, (.42,.29,.14), (.64,.49,.29), 4)
mottle(meadow, (.24,.28,.118), (.36,.39,.178), 1.5)
xs = [-16 + i*.20 for i in range(161)]
for side in (-1, 1):
    vertices, faces, indices = [], [], []
    for x in xs:
        jitter = .08*sin(1.9*x+side)+.04*sin(4.3*x)
        profiles = [(-.10, -.085), (.015, .006), (.11+jitter*.35, .046),
                    (.32+jitter, .22), (.58+jitter, .365), (.94+jitter, .408),
                    (1.42+jitter, .408), (11, .408)]
        for offset, height in profiles:
            vertices.append((x, edge(x, side) + side*offset, height))
    for col in range(len(xs)-1):
        for row in range(7):
            a = 8*col+row
            face = (a, a+8, a+9, a+1)
            faces.append(face if side == 1 else face[::-1])
            indices.append((0,0,0,1,1,2,2)[row])
    bank = mesh('Near bank' if side == -1 else 'Far bank', vertices, faces, [silt,sand,meadow], indices)
    for poly in bank.data.polygons:
        poly.use_smooth = True

water_mat = material('Jade water / advected surface', (.041,.31,.30), .28, .14)
vertices = [(x, water_y(x, j/24), 0) for x in xs for j in range(25)]
faces = [(i*25+j, (i+1)*25+j, (i+1)*25+j+1, i*25+j+1)
         for i in range(len(xs)-1) for j in range(24)]
river = mesh('River surface', vertices, faces, [water_mat])
uv = river.data.uv_layers.new(name='Stream coordinates')
for loop in river.data.loops:
    i, j = divmod(loop.vertex_index, 25)
    uv.data[loop.index].uv = (xs[i], j/24)
nodes, links = water_mat.node_tree.nodes, water_mat.node_tree.links
coords = nodes.new('ShaderNodeTexCoord')
separate = nodes.new('ShaderNodeSeparateXYZ')
links.new(coords.outputs['UV'], separate.inputs[0])


def math_node(operation, a, b):
    node = nodes.new('ShaderNodeMath')
    node.operation = operation
    for slot, value in zip(node.inputs, (a,b)):
        if isinstance(value, (int,float)):
            slot.default_value = value
        else:
            links.new(value, slot)
    return node.outputs[0]


u, d = separate.outputs[:2]
speed = math_node('ADD', .40, math_node('MULTIPLY', 1.09,
                  math_node('POWER', math_node('SINE', math_node('MULTIPLY', d, pi), 0), .78)))
time = nodes.new('ShaderNodeValue')
time.label = 'Seconds since frame 1'
time.outputs[0].default_value = 0
time.outputs[0].keyframe_insert('default_value', frame=1)
time.outputs[0].default_value = 47/12
time.outputs[0].keyframe_insert('default_value', frame=48)
for channel in time.id_data.animation_data.action.layers[0].strips[0].channelbag(
        time.id_data.animation_data.action_slot).fcurves:
    for key in channel.keyframe_points:
        key.interpolation = 'LINEAR'
advected = math_node('SUBTRACT', u, math_node('MULTIPLY', speed, time.outputs[0]))
combine = nodes.new('ShaderNodeCombineXYZ')
links.new(math_node('MULTIPLY', advected, 1.15), combine.inputs[0])
links.new(math_node('MULTIPLY', d, 34), combine.inputs[1])
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.45
noise.inputs['Detail'].default_value = 2
links.new(combine.outputs[0], noise.inputs['Vector'])
shore = math_node('POWER', math_node('ABSOLUTE', math_node('SUBTRACT',
                  math_node('MULTIPLY', d, 2), 1), 0), 4)
value = math_node('ADD', math_node('MULTIPLY', noise.outputs['Fac'], .53),
                  math_node('MULTIPLY', shore, .39))
ramp = nodes.new('ShaderNodeValToRGB')
for element, pos, color in [
    (ramp.color_ramp.elements[0], .08, (.018,.15,.166)),
    (ramp.color_ramp.elements[1], .72, (.25,.55,.44)),
    (ramp.color_ramp.elements.new(.35), .35, (.042,.31,.30)),
    (ramp.color_ramp.elements.new(.52), .52, (.11,.43,.375)),
]:
    element.position, element.color = pos, (*color, 1)
links.new(value, ramp.inputs[0])
bsdf = nodes.get('Principled BSDF')
links.new(ramp.outputs[0], bsdf.inputs['Base Color'])
links.new(ramp.outputs[0], bsdf.inputs['Emission Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .17
bump.inputs['Distance'].default_value = .043
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs[0], bsdf.inputs['Normal'])

# Tapered surface strokes travel on fixed streamlines, with no on-screen resets.
glints = [material('Current / '+str(i), color, .48, .35) for i, color in enumerate(
    [(.15,.46,.43), (.24,.60,.55), (.43,.70,.61), (.62,.79,.65)])]


def ribbon(name, points, widths, mat):
    vertices = []
    for i, p in enumerate(points):
        direction = Vector(points[min(i+1,len(points)-1)]) - Vector(points[max(0,i-1)])
        normal = Vector((-direction.y,direction.x,0)).normalized()
        vertices.extend(tuple(Vector(p)+normal*widths[i]*side) for side in (-1,1))
    faces = [(2*i,2*i+2,2*i+3,2*i+1) for i in range(len(points)-1)]
    return mesh(name, vertices, faces, [mat])


for i in range(92):
    x0 = rng.uniform(-14, 8)
    lane = rng.uniform(.033, .965)
    length = rng.uniform(.15,.95)
    width = rng.uniform(.011,.039)
    phase = rng.uniform(0, 2*pi)
    points = [(length*t, .038*sin(pi*t+phase)*sin(pi*t), .012)
              for t in [j/8 for j in range(9)]]
    stroke = ribbon('Drifting surface highlight', points,
                    [width*sin(pi*j/8)**.8 for j in range(9)],
                    rng.choices(glints, weights=(4,5,3,1))[0])
    track = []
    for f in range(1,49,3):
        x = x0 + flow(lane)*(f-1)/12
        track.append((f, (x,water_y(x,lane),0)))
    x = x0 + flow(lane)*47/12
    track.append((48,(x,water_y(x,lane),0)))
    animate(stroke, track, 'location')

stone_mats = [material('Shale '+str(i), c) for i,c in enumerate(
    [(.19,.235,.215), (.29,.32,.265), (.36,.33,.25), (.44,.39,.29)])]


def stone(name, x, y, z, scales):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=(x,y,z))
    obj = bpy.context.object
    obj.name = name
    for v in obj.data.vertices:
        v.co *= rng.uniform(.85,1.11)
    obj.scale = scales
    obj.rotation_euler[2] = rng.random()*pi
    for mat in stone_mats:
        obj.data.materials.append(mat)
    shade = rng.randrange(3)
    for poly in obj.data.polygons:
        poly.material_index = min(3, shade + int(rng.random()<.16))
        poly.use_smooth = True
    return obj


for side, groups in [(-1, [-5.0,-3.9,-.65,2.8,4.5]), (1,[-5,-3.4,-1.5,1.0,3.3,5.8])]:
    for x in groups:
        for i in range(rng.randint(3,7)):
            xx = x+rng.uniform(-.48,.48)
            off = rng.uniform(.11,.81)
            s = rng.uniform(.04,.24)
            stone('Bank cobble',xx,edge(xx,side)+side*off, min(.39, .04+(off-.10)*.68),
                  (s*1.35,s,s*.57))

# One stationary rock divides the current. Surface folds open on its lee side.
rx, ry = 3.12, water_y(3.12,.71)
rock = stone('Midstream slate',rx,ry,.035,(.43,.31,.24))
rock.rotation_euler[2] = -.16
for sign in (-1,1):
    points = [(rx-.39+1.56*t, ry+sign*(.11+.23*sin(pi*t*.64)), .018)
              for t in [j/24 for j in range(25)]]
    ribbon('Standing wake beside slate', points,
           [.029*sin(pi*j/24)**.77 for j in range(25)], glints[2])
ribbon('Upstream pressure ripple',
       [(rx-.43-.085*cos(a),ry+.32*sin(a),.019) for a in [-1.4+j*.14 for j in range(21)]],
       [.02*sin(pi*j/20) for j in range(21)],glints[2])

grasses = [material('Sedge '+str(i), c) for i,c in enumerate(
    [(.23,.29,.104),(.33,.37,.131),(.52,.49,.19),(.41,.44,.19)])]
grass_verts, grass_faces, grass_indices = [], [], []
for side, groups in [(-1,[-6,-4.6,-3.95,-.95,1.8,3.65,4.8,6]),
                     (1,[-6,-4.8,-3.8,-2,.1,1.6,2.45,4.6,5.95])]:
    for x in groups:
        for tuft in range(rng.randint(3,7)):
            xx = x+rng.uniform(-.49,.49)
            off = rng.uniform(.49,1.25)
            yy = edge(xx,side)+side*off
            z = min(.408,.33+(off-.49)*.35)-.015
            for blade in range(rng.randint(4,8)):
                a = rng.uniform(0,2*pi)
                h = rng.uniform(.14,.43)
                bend = rng.uniform(.055,.21)
                w = rng.uniform(.012,.032)
                bx,by = xx+rng.uniform(-.08,.08), yy+rng.uniform(-.08,.08)
                start = len(grass_verts)
                for t in (0,.27,.57,.83,1):
                    for s in (-1,1):
                        grass_verts.append((bx+bend*cos(a)*t*t-s*sin(a)*w*(1-t),
                                            by+bend*sin(a)*t*t+s*cos(a)*w*(1-t),z+h*t))
                grass_faces.extend([(start+2*i,start+2*i+1,start+2*i+3,start+2*i+2) for i in range(4)])
                grass_indices.extend([rng.randrange(4)]*4)
mesh('Sedge clumps along both banks', grass_verts, grass_faces, grasses, grass_indices)

# The ochre leaf is a small moving target for the watcher's gaze.
ochre = material('Floating alder leaf', (.83,.31,.048), .48, .12)
vein = material('Leaf midrib', (.96,.57,.16), .65, .12)
leaf_lane = .22
leaf_x = -1.94
leaf = mesh('Alder leaf',
    [(-.14,0,.003),(-.073,-.063,.014),(.022,-.065,.012),(.125,0,.027),
     (.04,.056,.021),(-.06,.065,.016),(-.012,0,.038)],
    [(i,(i+1)%6,6) for i in range(6)], [ochre])
midrib = ribbon('Leaf vein', [(-.12,0,.009),(-.012,0,.04),(.11,0,.03)],
                [.002,.006,.001], vein)
midrib.parent = leaf
leaf_track, leaf_turn = [], []
for f in range(1,49):
    t = (f-1)/12
    x = leaf_x + flow(leaf_lane)*t
    leaf_track.append((f,(x,water_y(x,leaf_lane)+.025*sin(4*t),.012+.005*sin(9*t))))
    leaf_turn.append((f,(.11*sin(5*t), .16*sin(3.8*t), .17+.42*sin(1.7*t))))
animate(leaf,leaf_track,'location')
animate(leaf,leaf_turn,'rotation_euler')

# Reuse the supplied KinemIQ CC0 v1.0 mannequin and planted Idle_relaxed.
asset = Path(__file__).resolve().parent / 'assets' / 'watcher.glb'
bpy.ops.import_scene.gltf(filepath=str(asset))
rig = next(obj for obj in bpy.context.selected_objects if obj.type == 'ARMATURE')
root = rig
while root.parent:
    root = root.parent
root.name = 'Watcher / planted on the sand shelf'
root.location = (-2.68, edge(-2.68,-1)-1.06, .4175)
root.rotation_mode = "XYZ"
root.rotation_euler.z = math.radians(135)
body = next(obj for obj in rig.children if obj.name.startswith('SuperHero'))
skin = material('Weathered copper skin', (.48,.245,.137))
jacket = material('Burnt orange field sweater', (.54,.135,.037))
pants = material('Indigo trousers', (.047,.093,.116))
boots = material('Dark leather boots', (.048,.037,.026))
hair = material('Dark umber hair', (.061,.032,.022))
ribbing = material('Sweater collar and cuffs', (.33,.077,.025))
body.data.materials.clear()
for mat in [skin,jacket,pants,boots,hair,ribbing]:
    body.data.materials.append(mat)
groups = {group.index:group.name for group in body.vertex_groups}
for poly in body.data.polygons:
    pos = sum((body.data.vertices[i].co for i in poly.vertices), Vector()) / len(poly.vertices)
    weights = {}
    for i in poly.vertices:
        for group in body.data.vertices[i].groups:
            name = groups[group.group]
            weights[name] = weights.get(name,0) + group.weight
    bone = max(weights, key=weights.get, default='')
    z = pos.z
    if bone.startswith(('Head','head','neck')):
        poly.material_index = 4 if z > 1.704 + .43*max(0,-pos.y-.11) else (5 if z < 1.515 else 0)
    elif bone.startswith(('hand','index','middle','thumb','ring','pinky')):
        poly.material_index = 0
    elif z < .155:
        poly.material_index = 3
    elif bone.startswith(('upperarm','lowerarm','clavicle')):
        poly.material_index = 1
    else:
        poly.material_index = 2 if z < 1.015 else 1
for obj in rig.children:
    if obj.name.startswith(('Eyebrows','Eyes')):
        obj.data.materials.clear()
        obj.data.materials.append(hair)

# Retiming one full idle breath keeps the contact in the source clip.
# Aim deltas are applied in armature space after each sampled idle pose.
animation = rig.animation_data
source = bpy.data.actions['Idle_relaxed']
animation.action = source
for track in animation.nla_tracks:
    track.mute = True
head = rig.pose.bones['Head']
scene.frame_set(1)
bpy.context.view_layer.update()
local_forward = head.matrix.to_quaternion().inverted() @ Vector((0,-1,0))
poses = []
for frame in range(1,49):
    source_frame = 30*(frame-1)/47
    scene.frame_set(int(source_frame), subframe=source_frame%1)
    target = Vector(leaf_track[frame-1][1])
    target.x += .12
    # Eyes carry some of the downward tilt. Keep the face readable in silhouette.
    target.z += .88
    world_to_rig = rig.matrix_world.inverted()
    eye = head.head + head.matrix.to_quaternion() @ local_forward * .095
    gaze = (world_to_rig @ target - eye).normalized()
    current = head.matrix.to_quaternion() @ local_forward
    turn = current.rotation_difference(gaze)
    baseline = head.matrix.copy()
    aim_matrix = Quaternion().slerp(turn, .90).to_matrix().to_4x4() @ baseline
    aim_matrix.translation = baseline.translation
    head.matrix = aim_matrix
    poses.append([(bone.location.copy(),bone.rotation_quaternion.copy(),bone.scale.copy())
                  for bone in rig.pose.bones])
animation.action = None
for frame, pose in enumerate(poses,1):
    for bone, (loc, rot, scale) in zip(rig.pose.bones,pose):
        bone.location, bone.rotation_quaternion, bone.scale = loc, rot, scale
        for prop in ('location','rotation_quaternion','scale'):
            bone.keyframe_insert(prop,frame=frame,group=bone.name)
animation.action.name = 'Planted idle and downstream gaze'

scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
