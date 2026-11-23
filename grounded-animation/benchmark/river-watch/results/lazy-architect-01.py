"""Build a four-second riverside scene with Blender 5.2."""
from math import cos, pi, sin
from pathlib import Path
from random import Random

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'
rng = Random(42)


def material(name, color, roughness=.82):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    surface = mat.node_tree.nodes.get('Principled BSDF')
    surface.inputs['Base Color'].default_value = mat.diffuse_color
    surface.inputs['Roughness'].default_value = roughness
    return mat


def mesh(name, vertices, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def pebble(name, center, scale, mat, detail=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=detail, location=center)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    ob.rotation_euler.z = rng.uniform(0, pi)
    ob.data.materials.append(mat)
    return ob


def shore(x):
    return .46 * sin(.43 * x + .38) + .16 * sin(.91 * x)


def bank_offset(x, side):
    return shore(x) + (2.30 + .23*cos(.38*x) if side == 1 else -1.62)


grass = material('Dry sage', (.27, .33, .18))
turf = material('Sunlit olive', (.32, .37, .21))
sand = material('Wet ochre sand', (.35, .245, .145))
clay = material('Dry clay at the waterline', (.46, .34, .21))
stone = material('Cool slate', (.12, .18, .176))
stone_light = material('Pale slate', (.21, .28, .265))
reed = material('Olive rushes', (.19, .25, .095))
reed_tip = material('Golden rushes', (.43, .36, .135))
water = material('Jade blue current', (.03, .28, .29), .36)
glints = [material('Water reflection ' + str(i), col) for i, col in enumerate(
    [(.115, .40, .40), (.21, .53, .50), (.37, .65, .56)])]
leaf_mat = material('Ochre willow leaf', (.87, .36, .05))
leaf_light = material('Gold willow leaf', (1.0, .61, .12))

# Continuous banks. The wet shelf meets the water below the dry top.
xs = [-24 + .30*i for i in range(161)]
for side in (-1, 1):
    sections = [(0, -.045), (.20, .018), (.46, .17), (.79, .35),
                (1.36, .39), (2.35, .43), (4.2, .5), (7.0, .57), (18, .66)]
    vertices = []
    for x in xs:
        for j, (distance, height) in enumerate(sections):
            height += min(j / 3, 1) * (.031*sin(1.3*x + .8*j) + .024*cos(.64*x-j))
            vertices.append((x, bank_offset(x, side) + side*distance, height))
    count = len(sections)
    faces = []
    for i in range(len(xs)-1):
        for j in range(count-1):
            a = i*count+j
            quad = (a, a+count, a+count+1, a+1)
            faces.append(quad if side == 1 else quad[::-1])
    bank = mesh('Near bank' if side == -1 else 'Far bank', vertices, faces, sand)
    for mat in (clay, grass, turf):
        bank.data.materials.append(mat)
    for poly in bank.data.polygons:
        row = poly.index % (count-1)
        poly.material_index = (0, 1, 1, 3, 2, 2, 2, 2)[row]
        poly.use_smooth = True

mesh('River surface', [(-24,-6,0), (24,-6,0), (24,7,0), (-24,7,0)],
     [(0,1,2,3)], water)
nodes, links = water.node_tree.nodes, water.node_tree.links
surface = nodes.get('Principled BSDF')
coords = nodes.new('ShaderNodeTexCoord')
mapping = nodes.new('ShaderNodeMapping')
mapping.inputs['Scale'].default_value = (.56, 4.6, 1)
links.new(coords.outputs['Object'], mapping.inputs['Vector'])
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.25
noise.inputs['Detail'].default_value = 2.0
links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .13
ramp.color_ramp.elements[0].color = (.017, .16, .187, 1)
ramp.color_ramp.elements[1].position = .87
ramp.color_ramp.elements[1].color = (.052, .34, .328, 1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
links.new(ramp.outputs['Color'], surface.inputs['Base Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .14
bump.inputs['Distance'].default_value = .025
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs['Normal'], surface.inputs['Normal'])
for frame in (1, 48):
    offset = mapping.inputs['Location']
    offset.default_value.x = -.56 * 1.08 * (frame-1)/12
    offset.keyframe_insert(data_path='default_value', frame=frame)


def path_motion(ob, start, lane, speed, height):
    for frame in [*range(1, 48, 4), 48]:
        x = start + speed*(frame-1)/12
        ob.location = (x, shore(x) + lane, height)
        ob.rotation_euler.z = .19*cos(.43*x + .38) + .145*cos(.91*x)
        ob.keyframe_insert(data_path='location', frame=frame)
        ob.keyframe_insert(data_path='rotation_euler', frame=frame)


def streak(name, length, width, mat, bend):
    vertices = []
    for j in range(13):
        t = j/12
        y = bend*sin(pi*t) + width*.15*sin(2*pi*t)
        radius = width * max(.015, sin(pi*t)**.75) * (1.3-.55*t)
        vertices.extend(((t*length, y-radius, 0), (t*length, y+radius, 0)))
    return mesh(name, vertices, [(2*j,2*j+2,2*j+3,2*j+1) for j in range(12)], mat)


for i in range(96):
    lane = rng.uniform(-1.53, 2.19)
    speed = .58 + .66*sin(pi*(lane+1.62)/4.0)
    ob = streak('Current highlight', rng.uniform(.19, .96), rng.uniform(.008, .029),
                rng.choices(glints, (47, 40, 13))[0], rng.uniform(-.035, .036))
    path_motion(ob, rng.uniform(-14, 10), lane, speed, .011 + i*.000018)


def floating_leaf(start, lane, scale):
    ob = mesh('Floating willow leaf',
              [(-.11,0,0), (-.037,-.048,0), (.047,-.032,0), (.12,0,0),
               (.045,.036,0), (-.033,.049,0), (0,0,.019)],
              [(i, (i+1)%6, 6) for i in range(6)], leaf_mat)
    ob.data.materials.append(leaf_light)
    for face in ob.data.polygons:
        face.material_index = int(face.index >= 3)
    ob.scale = (scale,)*3
    path_motion(ob, start, lane, 1.16, .031)
    return ob


leaf = floating_leaf(-3.9, .53, 1.17)
floating_leaf(-5.3, .82, .66)
floating_leaf(.2, 1.18, .61)

# River stones, short wakes, and a few broken clumps of rushes.
for x, lane, size in [(-4.7,1.63,.47), (1.15,1.89,.36), (3.67,-1.39,.39)]:
    y = shore(x)+lane
    pebble('Water-worn boulder', (x,y,.035), (size,size*.76,size*.55), stone)
    for sign in (-1, 1):
        wake = streak('Boulder wake', 2.4*size, .026, glints[1], -sign*.046)
        wake.location = (x+.20*size, y+sign*.52*size, .017)
        wake.rotation_euler.z = -sign*.095

for side, centers in [(-1, [-6.2,-4.7,-3.9,.4,2.4,4.8]),
                      (1, [-7.2,-5.0,-2.1,.25,2.6,4.7,6.6])]:
    for x in centers:
        for j in range(rng.randint(3, 6)):
            rx = x + rng.uniform(-.52, .52)
            distance = rng.uniform(.15, .62)
            y = bank_offset(rx, side)+side*distance
            size = rng.uniform(.06,.19)
            pebble('Shore pebble', (rx,y,.025 + .51*max(0,distance-.20)),
                   (size, size*rng.uniform(.55,.88), size*.52),
                   rng.choice([stone, stone_light, sand]))
        vertices, faces = [], []
        for j in range(rng.randint(9, 16)):
            rx = x + rng.uniform(-.35,.35)
            y = bank_offset(rx,side) + side*rng.uniform(.53,.75)
            z = .20
            h = rng.uniform(.19,.45)
            lean = rng.uniform(-.16,.19)
            angle = rng.uniform(0, pi)
            dx, dy = .022*cos(angle), .022*sin(angle)
            i = len(vertices)
            vertices.extend([(rx-dx,y-dy,z), (rx+dx,y+dy,z),
                             (rx+lean*.38+dx*.7,y+dy*.7,z+h*.58),
                             (rx+lean,y+side*.09,z+h),
                             (rx+lean*.38-dx*.7,y-dy*.7,z+h*.58)])
            faces.extend([(i,i+1,i+2,i+4), (i+4,i+2,i+3)])
        clump = mesh('Shore rushes', vertices, faces, reed)
        clump.data.materials.append(reed_tip)
        for poly in clump.data.polygons:
            poly.material_index = int(poly.index % 4 == 1)

# Reuse the relaxed pose and its weight shifts. Sample once to add a slow
# head turn in armature space, keeping the imported skinning and foot pose.
bpy.ops.import_scene.gltf(filepath=str(Path(__file__).resolve().parent / 'assets/watcher.glb'))
rig = next(ob for ob in bpy.context.selected_objects if ob.type == 'ARMATURE')
root = rig.parent.parent
root.name = 'Watcher'
root.rotation_euler.z = 2.63
root.location = (-2.48, bank_offset(-2.48,-1)-.87, .366)
idle = bpy.data.actions['Idle_relaxed']
rig.animation_data.use_nla = False
rig.animation_data.action = idle
rig.animation_data.action_slot = idle.slots[0]
head = rig.pose.bones['Head']
eyes = bpy.data.objects['Eyes']
samples = []
for frame in [*range(1,48,2), 48]:
    source = 2 + (frame-1)*26/47
    scene.frame_set(int(source), subframe=source%1)
    eyes_eval = eyes.evaluated_get(bpy.context.evaluated_depsgraph_get())
    eye_center = sum((v.co for v in eyes_eval.data.vertices), Vector())
    eye_center /= len(eyes_eval.data.vertices)
    to_rig = rig.matrix_world.inverted()
    eye_center = to_rig @ eyes_eval.matrix_world @ eye_center
    neck_axis = (head.tail - head.head).normalized()
    forward = eye_center - head.head
    forward -= neck_axis * forward.dot(neck_axis)
    leaf_x = -3.9 + 1.16*(frame-1)/12
    target = to_rig @ Vector((leaf_x, shore(leaf_x)+.53, .03))
    gaze = target - eye_center
    gaze.z *= .63
    basis = head.matrix.to_quaternion()
    adjustment = forward.rotation_difference(gaze)
    rotation = head.rotation_quaternion.copy() @ basis.inverted() @ adjustment @ basis
    samples.append((frame, [(bone, bone.location.copy(), bone.rotation_quaternion.copy(),
                              bone.scale.copy()) for bone in rig.pose.bones], rotation))
rig.animation_data_create()
rig.animation_data.action = bpy.data.actions.new('Watching the current')
for frame, poses, rotation in samples:
    for bone, location, quaternion, scale in poses:
        bone.location = location
        bone.rotation_quaternion = rotation if bone == head else quaternion
        bone.scale = scale
        for prop in ('location', 'rotation_quaternion', 'scale'):
            bone.keyframe_insert(data_path=prop, frame=frame)

jacket = material('Burnt orange pullover', (.64,.156,.038))
cuff = material('Deep rust hem and cuffs', (.34,.064,.019))
pants = material('Indigo trousers', (.042,.071,.118))
boots = material('Charcoal boots', (.045,.036,.033))
skin = material('Warm skin', (.52,.246,.125))
hair = material('Dark umber hair', (.050,.025,.017))
eye = material('Eyes', (.13,.084,.057))
body = bpy.data.objects['SuperHero_Male']
body.data.materials.clear()
for mat in (jacket, cuff, pants, boots, skin, hair):
    body.data.materials.append(mat)
for face in body.data.polygons:
    x,y,z = (sum(body.data.vertices[k].co[i] for k in face.vertices)/len(face.vertices)
             for i in range(3))
    hand = abs(x) > .29 and z < 1.04 and z > .66
    if z > 1.51:
        index = 5 if z > 1.704 or (z > 1.625 and y > -.029) else 4
    elif z > 1.47:
        index = 4
    elif hand:
        index = 4
    elif z < .125:
        index = 3
    elif z < .94:
        index = 2
    elif z < .99:
        index = 1
    else:
        index = 0
    face.material_index = index
for name, mat in [('Eyebrows', hair), ('Eyes', eye)]:
    ob = bpy.data.objects[name]
    ob.data.materials.clear()
    ob.data.materials.append(mat)


def aim(ob, target):
    ob.rotation_euler = (Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()


bpy.ops.object.camera_add(location=(3.5,-9.6,6.85))
camera = bpy.context.object
camera.name = 'Riverside composition'
aim(camera, (-.32,-.13,.28))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 10.9
scene.camera = camera

scene.world = bpy.data.worlds.new('Pale warm sky')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.49,.64,.74,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .38
bpy.ops.object.light_add(type='SUN', location=(-4,-4,8))
sun = bpy.context.object
sun.name = 'Afternoon sun'
sun.data.energy = 2.0
sun.data.color = (1,.82,.65)
sun.data.angle = .14
aim(sun,(0,0,0))
bpy.ops.object.light_add(type='AREA', location=(2,4,6))
fill = bpy.context.object
fill.name = 'Sky fill'
fill.data.energy = 450
fill.data.shape = 'DISK'
fill.data.size = 8
fill.data.color = (.68,.84,1)
aim(fill,(0,0,0))
scene.frame_set(1)
