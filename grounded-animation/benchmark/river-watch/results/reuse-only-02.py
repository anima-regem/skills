"""Build the river vignette with Blender 5.2 from factory startup."""

import math
import random
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, 48
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.view_settings.view_transform = 'AgX'
rng = random.Random(41)


def material(name, color, roughness=.87, glow=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Emission Color'].default_value = (*color, 1)
    shader.inputs['Emission Strength'].default_value = glow
    return mat


def mesh(name, verts, faces, mats):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    for mat in mats:
        data.materials.append(mat)
    return obj


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def linear(obj):
    animation = obj.animation_data
    action = animation.action
    for curve in action.layers[0].strips[0].channelbag(animation.action_slot).fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'


# KinemIQ Mannequin and Idle_relaxed, KinemIQ, CC0 1.0.
# https://github.com/Kinemiq/free-game-animations/releases/tag/v1.0
bpy.ops.import_scene.gltf(filepath=str(Path(__file__).resolve().parent / 'assets' / 'watcher.glb'))
rig = next(obj for obj in bpy.context.selected_objects if obj.type == 'ARMATURE')
root = rig.parent.parent
root.name = 'Watcher on the near bank'
root.location = (-2.85, -1.87, .388)
root.rotation_mode = 'XYZ'
root.rotation_euler.z = math.radians(143)
animation = rig.animation_data
for track in list(animation.nla_tracks):
    animation.nla_tracks.remove(track)
action = bpy.data.actions['Idle_relaxed'].copy()
action.name = 'Relaxed stance and downstream gaze'
animation.action = action
animation.action_slot = action.slots[0]
curves = action.layers[0].strips[0].channelbag(action.slots[0]).fcurves
for curve in curves:
    for key in curve.keyframe_points:
        key.co.x = 1 + key.co.x * 47 / 30
    curve.update()

head = rig.pose.bones['Head']
head_path = head.path_from_id('rotation_quaternion')
poses = []
for frame in range(1, 49):
    scene.frame_set(frame)
    t = (frame - 1) / 47
    follow = .5 - .5 * math.cos(math.pi * min(1, max(0, (t - .1) / .72)))
    axis = head.matrix.to_quaternion().inverted()
    turn = Quaternion(axis @ Vector((0, 0, 1)), math.radians(9 - 23 * follow))
    dip = Quaternion(axis @ Vector((1, 0, 0)), math.radians(13 + 5 * math.sin(math.pi * t)))
    poses.append(head.rotation_quaternion @ turn @ dip)
for curve in list(curves):
    if curve.data_path == head_path:
        curves.remove(curve)
for frame, rotation in enumerate(poses, 1):
    head.rotation_quaternion = rotation
    head.keyframe_insert(data_path='rotation_quaternion', frame=frame, group='Head')

jacket = material('Burnt saffron jacket', (.66, .245, .043))
trousers = material('Ink blue trousers', (.036, .068, .082))
boots = material('Dark leather', (.034, .023, .018))
skin = material('Warm terracotta', (.46, .225, .131))
cap = material('Dark wool cap', (.046, .035, .025))
body = bpy.data.objects['SuperHero_Male']
body.data.materials.clear()
for mat in (jacket, trousers, boots, skin, cap):
    body.data.materials.append(mat)
for face in body.data.polygons:
    x, y, z = face.center
    face.material_index = (4 if z > 1.727 else 3 if z > 1.526 or abs(x) > .705
                           else 2 if z < .14 else 1 if z < .93 else 0)
for name in ('Eyebrows', 'Eyes'):
    data = bpy.data.objects[name].data
    data.materials.clear()
    data.materials.append(cap)


def shore(x, far=False):
    if far:
        return 2.77 + .32 * math.sin(.5 * x + 1.1) + .10 * math.sin(1.35 * x)
    return -1.10 + .24 * math.sin(.69 * x + .2) + .10 * math.cos(1.35 * x)


grass = material('Sage meadow', (.27, .32, .15))
grass_shade = material('Olive meadow', (.235, .282, .13))
sand = material('Gold silt', (.47, .342, .171))
wet = material('Wet clay', (.217, .163, .089))

for far in (False, True):
    sign = 1 if far else -1
    verts = []
    faces = []
    layers = ((-.10, -.085), (.04, .03), (.23, .17), (.43, .378), (1.3, .378),
              (2.6, .408), (4.0, .447), (8, .47))
    for i in range(121):
        x = -15 + .25 * i
        for j, (offset, height) in enumerate(layers):
            relief = .017 * math.sin(1.5 * x + j) * (j != 4)
            verts.append((x, shore(x, far) + sign * offset, height + relief))
        if i:
            for j in range(len(layers) - 1):
                a = (i - 1) * len(layers) + j
                quad = (a, a + len(layers), a + len(layers) + 1, a + 1)
                faces.append(quad if far else quad[::-1])
    bank = mesh('Far bank' if far else 'Near bank', verts, faces, [wet, sand, grass, grass_shade])
    for face in bank.data.polygons:
        row = face.index % (len(layers) - 1)
        face.material_index = min(row, 2) if row < 3 else (3 if row == 3 and far else 2)
        face.use_smooth = True

water = material('River | moving satin surface', (.027, .255, .30), .28)
nodes = water.node_tree.nodes
links = water.node_tree.links
shader = nodes.get('Principled BSDF')
texcoord = nodes.new('ShaderNodeTexCoord')
shift = nodes.new('ShaderNodeVectorMath')
shift.operation = 'ADD'
links.new(texcoord.outputs['Object'], shift.inputs[0])
for frame, distance in ((1, 0), (48, -5.8)):
    shift.inputs[1].default_value = (distance, 0, 0)
    shift.inputs[1].keyframe_insert('default_value', frame=frame)
linear(water.node_tree)
stretch = nodes.new('ShaderNodeVectorMath')
stretch.operation = 'MULTIPLY'
stretch.inputs[1].default_value = (.49, 3.6, 1)
links.new(shift.outputs[0], stretch.inputs[0])
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 2.25
noise.inputs['Detail'].default_value = 2.1
links.new(stretch.outputs[0], noise.inputs['Vector'])
palette = nodes.new('ShaderNodeValToRGB')
palette.color_ramp.elements[0].position = .20
palette.color_ramp.elements[0].color = (.019, .151, .18, 1)
palette.color_ramp.elements[1].position = .83
palette.color_ramp.elements[1].color = (.073, .393, .406, 1)
links.new(noise.outputs['Fac'], palette.inputs[0])
links.new(palette.outputs[0], shader.inputs['Base Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .17
bump.inputs['Distance'].default_value = .031
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs[0], shader.inputs['Normal'])
mesh('Continuous water surface', [(-16, -3, 0), (16, -3, 0), (16, 5, 0), (-16, 5, 0)],
     [(0, 1, 2, 3)], [water])

silver = material('Light turquoise ripples', (.23, .54, .52), .6, .18)
foam = material('Pearl ripples', (.52, .72, .65), .65, .12)
leaf_mat = material('Amber leaves', (.74, .35, .053), .56)
leaf_light = material('Sunlit leaf fold', (.95, .55, .10), .56)


def glide(obj, x, offset, speed, z):
    for frame in (1, 48):
        distance = speed * (frame - 1) / 12
        obj.location = (x + distance, shore(x + distance) + offset, z)
        obj.keyframe_insert(data_path='location', frame=frame)
    # Sample the curved lanes in between the endpoints.
    for frame in range(4, 48, 3):
        distance = speed * (frame - 1) / 12
        obj.location = (x + distance, shore(x + distance) + offset, z)
        obj.keyframe_insert(data_path='location', frame=frame)
    linear(obj)


for i in range(112):
    x = rng.uniform(-12, 7)
    offset = rng.uniform(.18, 3.43)
    length = rng.uniform(.14, .81)
    width = rng.uniform(.009, .037)
    bend = rng.uniform(-.046, .046)
    verts = [(-.67 * length, -bend, 0), (-.22 * length, width * .55, 0),
             (.19 * length, width + bend, 0), (.33 * length, bend, 0),
             (.12 * length, -.45 * width + bend, 0), (-.29 * length, -.25 * width, 0)]
    stroke = mesh('Advecting surface streak', verts, [tuple(range(5, -1, -1))],
                  [foam if i % 8 == 0 else silver])
    speed = .91 + .72 * math.sin(math.pi * offset / 3.8)
    glide(stroke, x, offset, speed, .012)

for i, (x, offset) in enumerate(((-5.4, .86), (-2.8, 1.5), (-4.26, 2.5), (.4, 2.85), (-8.2, 1.63))):
    leaf = mesh('Drifting willow leaf', [(-.135, 0, .008), (-.04, -.04, .002), (.066, -.028, 0),
                (.113, .008, .007), (.045, .043, .009), (-.048, .034, .005), (0, 0, .024)],
                [(6, j, (j + 1) % 6) for j in range(6)], [leaf_mat, leaf_light])
    for face in leaf.data.polygons:
        face.material_index = int(face.index >= 3)
    glide(leaf, x, offset, 1.23 + .10 * i, .026)
    for frame in (1, 13, 25, 37, 48):
        leaf.rotation_euler.z = .44 * math.sin(frame * .12 + i)
        leaf.rotation_euler.x = .12 * math.cos(frame * .21 + i)
        leaf.keyframe_insert(data_path='rotation_euler', frame=frame)

stone = [material('Warm slate', (.22, .233, .20)), material('Pale slate', (.34, .332, .267))]


def rock(x, y, z, size):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=(x, y, z))
    obj = bpy.context.object
    obj.name = 'Rounded river stone'
    obj.scale = size
    obj.rotation_euler.z = rng.uniform(-1, 1)
    obj.data.materials.append(rng.choice(stone))
    for face in obj.data.polygons:
        face.use_smooth = True


for x, y, z, size in ((1.22, 1.66, -.055, (.39, .27, .22)),
                      (1.61, 1.83, -.042, (.24, .17, .13)),
                      (-4.04, -1.70, .32, (.38, .23, .17)),
                      (3.15, -1.58, .30, (.30, .23, .16)),
                      (-2.1, 3.43, .33, (.43, .31, .20)),
                      (4.2, 3.45, .34, (.37, .29, .16))):
    rock(x, y, z, size)

# Split ribbons of disturbed water remain anchored at the midstream stones.
for sign in (-1, 1):
    for lane in range(2):
        verts = []
        faces = []
        for i in range(28):
            t = i / 27
            x = .92 + (1.57 + .18 * lane) * t
            y = 1.69 + sign * (.13 + .072 * lane + .26 * math.sin(t * 1.88))
            width = .025 * math.sin(math.pi * t) * (1 - .37 * lane)
            verts.extend([(x, y - width, .019), (x, y + width, .019)])
            if i:
                j = i * 2
                faces.append((j - 2, j, j + 1, j - 1))
        mesh('Water curling around slate', verts, faces, [foam if lane == 0 else silver])

reeds = [material('Golden reed tips', (.44, .385, .115)), material('Reed green', (.15, .235, .078))]
verts, faces = [], []
for x, far, count in [(-4.65, False, 19), (-3.92, False, 13), (-1.25, False, 13),
                      (2.44, False, 19), (4.55, False, 23), (-4.9, True, 24),
                      (-2.0, True, 21), (.5, True, 12), (3.8, True, 21)]:
    for _ in range(count):
        px = x + rng.uniform(-.36, .36)
        py = shore(px, far) + (1 if far else -1) * rng.uniform(.42, .88)
        height = rng.uniform(.13, .42)
        bend = rng.uniform(-.16, .16)
        width = rng.uniform(.013, .037)
        j = len(verts)
        verts.extend([(px - width, py, .362), (px + width, py, .362),
                      (px + bend * .40 + width * .57, py + .023, .36 + height * .60),
                      (px + bend, py + .071, .36 + height),
                      (px + bend * .40 - width * .57, py + .023, .36 + height * .60)])
        faces.append(tuple(range(j, j + 5)))
tufts = mesh('Sparse grasses on both banks', verts, faces, reeds)
for face in tufts.data.polygons:
    face.material_index = int(rng.random() < .74)


world = bpy.data.worlds.new('Cool skylight')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.49, .62, .74, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .48
scene.world = world

sun = bpy.data.lights.new('Low warm sun', 'SUN')
sun.energy = 2.18
sun.angle = math.radians(11)
sun.color = (1, .84, .64)
sun_obj = bpy.data.objects.new(sun.name, sun)
scene.collection.objects.link(sun_obj)
sun_obj.location = (-4, 1, 8)
point_at(sun_obj, (0, -2, 0))

fill = bpy.data.lights.new('Open sky fill', 'AREA')
fill.energy = 320
fill.shape = 'DISK'
fill.size = 8
fill.color = (.71, .85, 1)
fill_obj = bpy.data.objects.new(fill.name, fill)
scene.collection.objects.link(fill_obj)
fill_obj.location = (2, -4, 7)
point_at(fill_obj, (0, 0, 0))

camera = bpy.data.cameras.new('Riverbank composition')
camera.type = 'ORTHO'
camera.ortho_scale = 10.65
camera_obj = bpy.data.objects.new(camera.name, camera)
scene.collection.objects.link(camera_obj)
camera_obj.location = (1.34, -9, 7.55)
point_at(camera_obj, (0, .28, .26))
scene.camera = camera_obj
scene.frame_set(1)
