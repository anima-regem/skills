import math
import random

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
rng = random.Random(42)


def material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return mat


def mesh(name, vertices, faces, *materials):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    for mat in materials:
        data.materials.append(mat)
    return obj


def oval(name, pos, scale, mat, parent=None, facets=False):
    if facets:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12)
    obj = bpy.context.object
    obj.name, obj.parent, obj.location, obj.scale = name, parent, pos, scale
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = not facets
    return obj


def joint(name, pos, parent=None):
    obj = bpy.data.objects.new(name, None)
    scene.collection.objects.link(obj)
    obj.parent, obj.location = parent, pos
    return obj


def limb(name, a, b, width, depth, mat, parent):
    direction = Vector(b) - Vector(a)
    obj = oval(name, (Vector(a) + Vector(b)) / 2,
               (width, depth, direction.length / 2 + width * 0.48), mat, parent)
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()


def edge(x):
    return -1.2 + 0.38 * math.sin(x * 0.49) + 0.28 * math.cos(x * 0.91)


def far_edge(x):
    return 5.4 + 0.62 * math.sin(x * 0.35 + 1)


grass = material('Moss green', (0.24, 0.30, 0.105))
far_grass = material('Meadow sage', (0.27, 0.34, 0.17))
sand = material('Ochre silt', (0.44, 0.30, 0.16))
wet = material('Wet silt', (0.23, 0.22, 0.11))
stone = material('Slate', (0.19, 0.24, 0.22))
stone_light = material('Pale slate', (0.32, 0.36, 0.28))
reeds = material('Rush green', (0.18, 0.26, 0.085))
tips = material('Dry rush', (0.43, 0.45, 0.19))
wood = material('Bark', (0.18, 0.105, 0.062))
canopy = material('Willow green', (0.20, 0.32, 0.15))
canopy_light = material('Willow tips', (0.32, 0.43, 0.18))

for name, boundary, side, height, turf in (
    ('Near bank', edge, -1, 0.42, grass),
    ('Far bank', far_edge, 1, 0.52, far_grass),
):
    profile = [(-0.23, -0.20), (0, 0.035), (0.32, height * 0.65),
               (0.72, height), (22, height)]
    vertices = [(x, boundary(x) + side * offset, z)
                for x in (i / 4 for i in range(-120, 121)) for offset, z in profile]
    faces = [(i, i + 5, i + 6, i + 1) for i in range(1200) if i % 5 != 4]
    if side < 0:
        faces = [face[::-1] for face in faces]
    bank = mesh(name, vertices, faces, wet, sand, turf)
    for index, face in enumerate(bank.data.polygons):
        face.material_index = min(index % 4, 2)

water = material('River | moving surface', (0.045, 0.31, 0.34), 0.28)
mesh('River', [(-32, -4, 0), (32, -4, 0), (32, 8, 0), (-32, 8, 0)],
     [(0, 1, 2, 3)], water)
nodes = water.node_tree.nodes
link = water.node_tree.links.new
coordinates = nodes.new('ShaderNodeTexCoord')
drift = nodes.new('ShaderNodeVectorMath')
drift.operation = 'ADD'
link(coordinates.outputs['Object'], drift.inputs[0])
drift.inputs[1].driver_add('default_value', 0).driver.expression = '-0.105*(frame-1)'
stretch = nodes.new('ShaderNodeVectorMath')
stretch.operation = 'MULTIPLY'
stretch.inputs[1].default_value = (0.55, 4.8, 1)
link(drift.outputs[0], stretch.inputs[0])
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.7
noise.inputs['Detail'].default_value = 2
link(stretch.outputs[0], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.18
ramp.color_ramp.elements[0].color = (0.021, 0.20, 0.25, 1)
ramp.color_ramp.elements[1].position = 0.84
ramp.color_ramp.elements[1].color = (0.12, 0.46, 0.45, 1)
link(noise.outputs['Fac'], ramp.inputs[0])
shader = nodes.get('Principled BSDF')
link(ramp.outputs[0], shader.inputs['Base Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = 0.2
bump.inputs['Distance'].default_value = 0.025
link(noise.outputs['Fac'], bump.inputs['Height'])
link(bump.outputs[0], shader.inputs['Normal'])

glint = material('Jade ripples', (0.22, 0.53, 0.51))
foam = material('Pale ripples', (0.49, 0.72, 0.65))
leaf = material('Floating ochre leaves', (0.80, 0.39, 0.075))


def ribbon(points, width, mat, parent):
    vertices = []
    for i, (x, y) in enumerate(points):
        half = width * math.sin(math.pi * i / (len(points) - 1)) ** 0.8
        vertices.extend([(x, y - half, 0.013), (x, y + half, 0.013)])
    obj = mesh('Surface ripple', vertices,
               [(i, i + 2, i + 3, i + 1) for i in range(0, len(vertices) - 2, 2)], mat)
    obj.parent = parent


for band, (y_min, y_max, speed) in enumerate(
        [(-0.48, 0.72, 3.1), (0.72, 3.65, 5.4), (3.65, 4.54, 3.8)]):
    flow = joint('Downstream current ' + str(band + 1), (0, 0, 0))
    flow.driver_add('location', 0).driver.expression = f'{speed}*(frame-1)/47'
    for _ in range((45, 100, 37)[band]):
        x, y = rng.uniform(-17, 9), rng.uniform(y_min, y_max)
        length = rng.uniform(0.22, 1.18)
        bend = rng.uniform(-0.055, 0.055)
        ribbon([(x + length * i / 6, y + bend * math.sin(i * math.pi / 6))
                for i in range(7)], rng.uniform(0.012, 0.028),
               foam if rng.random() < 0.23 else glint, flow)
    for x, y in [(-6.2, 0.2), (-2.4, 1.55), (-6.3, 2.85), (1.8, 2.6), (-3.8, 4.15)]:
        if y_min < y < y_max:
            oval('Drifting leaf', (x, y, 0.021), (0.125, 0.064, 0.019), leaf, flow)
            for side in (-1, 1):
                ribbon([(x - 0.76 + i * 0.1, y + side * (0.19 - 0.022 * i))
                        for i in range(8)], 0.017, foam, flow)

for x, y, size in [(-6, -1.60, 0.36), (-2.2, -1.73, 0.26), (0.1, -0.48, 0.29),
                   (3.9, -1.71, 0.34), (4.45, -1.86, 0.23), (3.3, 4.8, 0.54),
                   (3.9, 5.0, 0.33), (-4.4, 4.83, 0.32)]:
    oval('Shore stone', (x, y, 0.16), (size * 1.4, size, size * 0.82),
         rng.choice((stone, stone_light)), facets=True)

vertices, blades = [], []
for boundary, side, base in [(edge, -1, 0.42), (far_edge, 1, 0.52)]:
    for _ in range(78):
        x = rng.uniform(-11, 11)
        y = boundary(x) + side * rng.uniform(0.75, 2.6)
        if (x + 3.75) ** 2 + (y + 2.65) ** 2 < 0.65 ** 2 and side < 0:
            continue
        for _ in range(rng.randint(4, 8)):
            bx, by = x + rng.uniform(-0.16, 0.16), y + rng.uniform(-0.12, 0.12)
            dx, dy = rng.uniform(-0.16, 0.16), rng.uniform(-0.12, 0.12)
            h, w = rng.uniform(0.11, 0.44), rng.uniform(0.017, 0.037)
            i = len(vertices)
            vertices.extend([(bx-w, by, base), (bx+w, by, base),
                             (bx+dx*0.34+w*0.6, by+dy*0.34, base+h*0.59),
                             (bx+dx, by+dy, base+h),
                             (bx+dx*0.34-w*0.6, by+dy*0.34, base+h*0.59)])
            blades.append((i, i+1, i+2, i+3, i+4))
tufts = mesh('Bank grasses', vertices, blades, reeds, tips)
for face in tufts.data.polygons:
    face.material_index = rng.randrange(2)

for x, y, scale in [(-7.1, 6.5, 1.15), (-5.9, 6.75, 0.8),
                    (5.2, 6.25, 1.0), (6.45, 6.55, 1.35)]:
    tree = joint('Willow', (x, y, 0.52))
    tree.scale = (scale,) * 3
    limb('Trunk', (0, 0, 0), (0.13, 0, 1.35), 0.085, 0.09, wood, tree)
    for dx, dy, z, size in [(-0.46, 0.06, 1.45, 0.60), (0.48, 0.04, 1.62, 0.66),
                            (0.08, 0, 1.96, 0.68), (0.02, -0.38, 1.45, 0.52)]:
        limb('Bough', (0.09, 0, 0.75), (dx, dy, z), 0.042, 0.042, wood, tree)
        oval('Willow crown', (dx, dy, z), (size, size * 0.76, size * 0.91),
             rng.choice((canopy, canopy_light)), tree, facets=True)

ochre = material('Marigold jacket', (0.83, 0.28, 0.038))
cuff = material('Jacket binding', (0.46, 0.127, 0.026))
pants = material('Ink trousers', (0.048, 0.081, 0.087))
boot = material('Hiking boots', (0.10, 0.063, 0.047))
sole = material('Boot soles', (0.039, 0.033, 0.028))
skin = material('Warm clay', (0.55, 0.29, 0.17))
hair = material('Dark hair', (0.075, 0.040, 0.026))
cap = material('Brick cap', (0.45, 0.095, 0.055))
pack = material('Canvas daypack', (0.17, 0.27, 0.21))
person = joint('Watcher | feet planted', (-3.75, -2.65, 0.42))
person.rotation_euler.z = -0.51
person.scale = (1.19,) * 3
for side in (-1, 1):
    x = side * 0.132
    y = side * 0.055
    oval('Boot sole', (x, y+0.045, 0.043), (0.106, 0.192, 0.042), sole, person)
    oval('Boot upper', (x, y+0.033, 0.093), (0.104, 0.177, 0.081), boot, person)
    limb('Trouser leg', (x, y, 0.14), (side*0.112, 0, 0.93), 0.105, 0.109, pants, person)

body = joint('Upper body', (0, 0, 0.85), person)
oval('Jacket', (0, 0.007, 0.29), (0.278, 0.17, 0.347), ochre, body)
oval('Jacket hem', (0, 0, 0.082), (0.235, 0.147, 0.086), cuff, body)
oval('Folded hood', (0, -0.093, 0.53), (0.183, 0.143, 0.106), cuff, body)
oval('Canvas pack', (0, -0.177, 0.30), (0.186, 0.108, 0.216), pack, body)
oval('Pack pocket', (0, -0.251, 0.244), (0.138, 0.044, 0.101), canopy_light, body)
for side in (-1, 1):
    shoulder = (side*0.231, 0, 0.457)
    elbow = (side*0.312, -0.012, 0.238)
    wrist = (side*0.275, 0.061, 0.065)
    limb('Upper sleeve', shoulder, elbow, 0.093, 0.091, ochre, body)
    limb('Lower sleeve', elbow, wrist, 0.073, 0.075, ochre, body)
    oval('Hand', (wrist[0], wrist[1], 0.032), (0.060, 0.048, 0.083), skin, body)
    limb('Pack strap', (side*0.15, 0.09, 0.51), (side*0.164, 0.149, 0.224),
         0.025, 0.021, pack, body)

oval('Neck', (0, 0.024, 0.593), (0.080, 0.075, 0.106), skin, body)
head = joint('Head | follows the current', (0, 0.05, 0.62), body)
oval('Face', (0, 0, 0.136), (0.137, 0.128, 0.168), skin, head)
oval('Hair', (0, -0.052, 0.167), (0.142, 0.095, 0.153), hair, head)
for side in (-1, 1):
    oval('Ear', (side*0.128, 0.002, 0.123), (0.026, 0.035, 0.043), skin, head)
oval('Nose', (0, 0.122, 0.132), (0.031, 0.039, 0.036), skin, head)
oval('Cap crown', (0, -0.009, 0.242), (0.147, 0.142, 0.093), cap, head)
oval('Cap visor', (0, 0.111, 0.221), (0.113, 0.141, 0.021), cap, head)
for frame, turn, tilt, lean in [(1, 0.56, -0.25, -0.045), (10, 0.49, -0.33, -0.070),
                                 (26, 0.06, -0.36, -0.086), (48, -0.47, -0.25, -0.050)]:
    head.rotation_euler = (tilt, 0, turn)
    body.rotation_euler = (lean, 0.014, turn * 0.12)
    head.keyframe_insert(data_path='rotation_euler', frame=frame)
    body.keyframe_insert(data_path='rotation_euler', frame=frame)


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


bpy.ops.object.camera_add(location=(0.0, -12.8, 9.3))
scene.camera = bpy.context.object
scene.camera.name = 'Riverbank view'
aim(scene.camera, (0, 0.95, 0.1))
scene.camera.data.type = 'ORTHO'
scene.camera.data.ortho_scale = 13.8

scene.world = bpy.data.worlds.new('Soft blue sky')
scene.world.node_tree.nodes.get('Background').inputs[0].default_value = (0.53, 0.69, 0.80, 1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value = 0.36
bpy.ops.object.light_add(type='SUN', location=(-5, -4, 8))
sun = bpy.context.object
sun.data.energy, sun.data.angle, sun.data.color = 2.0, 0.22, (1, 0.85, 0.67)
aim(sun, (0, 0, 0))
bpy.ops.object.light_add(type='AREA', location=(2, 4, 8))
fill = bpy.context.object
fill.data.energy, fill.data.shape, fill.data.size = 750, 'DISK', 9
fill.data.color = (0.68, 0.86, 1)
aim(fill, (0, 0, 0))

scene.frame_set(1)
first_turn = head.rotation_euler.z
scene.frame_set(48)
assert head.rotation_euler.z < first_turn and flow.location.x > 0 and scene.camera
scene.frame_set(1)
