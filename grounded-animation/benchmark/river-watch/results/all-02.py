"""Four-second river study. Run with Blender in background mode."""
from math import atan2, cos, hypot, pi, radians, sin
from pathlib import Path
from random import Random

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
rng = Random(21)


def material(name, color, roughness=.82):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
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


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def shore(x, side):
    return side * (2.47 + .21 * sin(.57 * x + side) + .12 * cos(1.02 * x - side)) + .30


water = material('River · glacial blue', (.027, .29, .37), .32)
nodes, links = water.node_tree.nodes, water.node_tree.links
coords = nodes.new('ShaderNodeTexCoord')
scale = nodes.new('ShaderNodeVectorMath')
scale.operation = 'MULTIPLY'
scale.inputs[1].default_value = (.55, 3.7, 1)
links.new(coords.outputs['Object'], scale.inputs[0])
offset = nodes.new('ShaderNodeVectorMath')
offset.operation = 'ADD'
links.new(scale.outputs[0], offset.inputs[0])
offset.inputs[1].driver_add('default_value', 0).driver.expression = '-0.054*(frame-1)'
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.75
noise.inputs['Detail'].default_value = 2.0
links.new(offset.outputs[0], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .19
ramp.color_ramp.elements[0].color = (.016, .145, .213, 1)
ramp.color_ramp.elements[1].position = .81
ramp.color_ramp.elements[1].color = (.085, .405, .448, 1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
shader = nodes.get('Principled BSDF')
links.new(ramp.outputs[0], shader.inputs['Base Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .16
bump.inputs['Distance'].default_value = .054
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs[0], shader.inputs['Normal'])
mesh('Continuous water surface', [(-23, -8, 0), (23, -8, 0),
                                 (23, 9, 0), (-23, 9, 0)], [(0, 1, 2, 3)], [water])

sand = material('Wet ochre', (.34, .24, .12))
silt = material('Sand · warm edge', (.54, .402, .217))
grass = material('Meadow · sage', (.235, .32, .137))
grass_light = material('Meadow · lichen', (.251, .337, .148))
for side in (-1, 1):
    verts, faces = [], []
    sections = [(-.23, -.09), (.02, .026), (.24, .10), (.52, .26),
                (.94, .32), (1.8, .32), (3.4, .32), (7, .34), (20, .36)]
    width = len(sections)
    for i in range(117):
        x = -20 + i * .35
        for d, z in sections:
            edge = shore(x, side)
            verts.append((x, edge + side * (d + max(d, 0) * .04 * sin(2.3 * x)),
                          z + (.019 * sin(2.1 * x + d) if d < .94 else 0)))
        if i:
            for j in range(width - 1):
                k = (i - 1) * width + j
                face = (k, k + width, k + width + 1, k + 1)
                faces.append(face if side == 1 else face[::-1])
    bank = mesh('Near bank' if side == -1 else 'Far bank', verts, faces,
                [sand, silt, grass, grass_light])
    for p in bank.data.polygons:
        band = p.index % (width - 1)
        p.material_index = [0, 1, 1, 2, 2, 2, 2, 2][band]
        if band >= 3 and rng.random() < .12:
            p.material_index = 3
        p.use_smooth = True

stone = [material('Slate', (.177, .222, .214)), material('Warm slate', (.275, .28, .218)),
         material('Basalt', (.105, .156, .157))]


def rock(name, loc, dims, mat):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    for v in obj.data.vertices:
        v.co *= rng.uniform(.84, 1.14)
    obj.scale = dims
    obj.rotation_euler.z = rng.uniform(0, pi)
    obj.data.materials.append(mat)
    return obj


for i in range(57):
    x = rng.uniform(-12, 12)
    side = rng.choice((-1, 1))
    d = rng.uniform(.04, .67)
    s = rng.uniform(.041, .14)
    rock('Shore pebble', (x, shore(x, side) + side * d, .026 + .40 * d),
         (s, s * rng.uniform(.58, .94), s * .48), rng.choice(stone))

for x, y, size in [(-4.1, 2.22, .39), (-3.72, 2.38, .23), (2.02, -.87, .34),
                   (2.25, -.98, .24), (4.8, 2.4, .43), (-5.2, -2.35, .51)]:
    rock('River stone', (x, y, .04), (size, size * .67, size * .52), rng.choice(stone))

reeds = [material('Rush · olive', (.173, .249, .069)),
         material('Rush · straw', (.44, .374, .12)),
         material('Rush · shadow', (.092, .179, .087))]
verts, faces, indices = [], [], []
for i in range(152):
    x = rng.uniform(-12, 12)
    side = rng.choice((-1, 1))
    d = rng.uniform(.49, 2.3)
    y = shore(x, side) + side * d
    if side == -1 and abs(x + 2.65) < .56 and abs(y + 3.20) < .44:
        continue
    z = min(.32, .16 + .18 * d)
    height = rng.uniform(.10, .38)
    for j in range(rng.randint(4, 9)):
        angle = rng.uniform(0, 2 * pi)
        dx, dy = cos(angle), sin(angle)
        h = height * rng.uniform(.53, 1.2)
        w = rng.uniform(.012, .03)
        bend = h * rng.uniform(.19, .62)
        k = len(verts)
        for t, f in ((0, 1), (.48, .72), (.79, .36)):
            cx, cy = x + dx * (.023 + bend * t * t), y + dy * (.023 + bend * t * t)
            verts.extend([(cx - dy * w * f, cy + dx * w * f, z + h * t),
                          (cx + dy * w * f, cy - dx * w * f, z + h * t)])
        verts.append((x + dx * bend, y + dy * bend, z + h))
        faces.extend([(k, k+1, k+3, k+2), (k+2, k+3, k+5, k+4), (k+4, k+5, k+6)])
        indices.extend([rng.randrange(3)] * 3)
rushes = mesh('Bankside rushes', verts, faces, reeds)
for face, index in zip(rushes.data.polygons, indices):
    face.material_index = index

glints = [material('Pale current', (.20, .54, .55), .42),
          material('Silver current', (.42, .70, .66), .40),
          material('Deep current', (.059, .30, .36), .46)]


def ribbon(verts, faces, x, y, length, width, phase, wake=False):
    k = len(verts)
    for i in range(13):
        t = i / 12
        taper = max(.012, sin(pi * t)) ** .75
        curve = (.061 * sin(pi * t + phase) if not wake else .30 * (1 - t) ** 2)
        verts.extend([(x + t * length, y + curve + w * width * taper, .017)
                      for w in (-1, 1)])
        if i:
            a = k + 2 * i
            faces.append((a-2, a, a+1, a-1))


# Current is slower in the shallows. Surface shapes are deliberately graphic.
for lane in range(12):
    y = -1.89 + lane * .365
    speed = .62 + .60 * sin(pi * (lane + 1) / 13)
    verts, faces, indices = [], [], []
    for i in range(33):
        x = -17 + i * .93 + rng.uniform(-.37, .37)
        length = rng.uniform(.23, 1.26)
        ribbon(verts, faces, x, y + rng.uniform(-.12, .12), length,
               rng.uniform(.012, .032), rng.uniform(0, 2*pi))
        indices.extend([rng.choices([0, 1, 2], [5, 2, 4])[0]] * 12)
    obj = mesh(f'Advecting surface glints {lane + 1:02}', verts, faces, glints)
    obj.driver_add('location', 0).driver.expression = f'{speed / 12:.7f}*(frame-1)'
    for p, index in zip(obj.data.polygons, indices):
        p.material_index = index

for x, y, s in [(-4.1, 2.22, .39), (2.02, -.87, .34), (4.8, 2.4, .43)]:
    verts, faces = [], []
    for d in (.08, .20):
        ribbon(verts, faces, x-.11, y-s-d, s*4.2, .021, 0, wake=True)
    mesh('Attached eddy lip', verts, faces, glints[:1])

leaf_mat = material('Leaf · amber', (.85, .29, .036))
vein_mat = material('Leaf · gold fold', (1, .56, .095))
for i, (x, y, s) in enumerate([(-2.65, -.91, .19), (-6.2, .47, .115), (.6, 1.43, .108)]):
    leaf = mesh('Drifting leaf', [(-s, 0, 0), (-s*.28, s*.41, .004), (s*.45, s*.28, .006),
                                  (s, 0, .012), (s*.27, -s*.34, .01),
                                  (-s*.35, -s*.31, .002), (0, 0, .04)],
                [(j, (j+1) % 6, 6) for j in range(6)], [leaf_mat, vein_mat])
    for j in (0, 1, 2):
        leaf.data.polygons[j].material_index = 1
    for axis, expression in enumerate([f'{x} + .099*(frame-1)',
                                       f'{y} + .09*sin((frame-1)*.12+{i})',
                                       f'.037 + .009*sin((frame-1)*.25+{i})']):
        leaf.driver_add('location', axis).driver.expression = expression
    leaf.driver_add('rotation_euler', 2).driver.expression = f'.35*sin((frame-1)*.137+{i})'

# The bundled KinemIQ CC0 idle supplies the relaxed stance and shoulder motion.
bpy.ops.import_scene.gltf(filepath=str(Path(__file__).resolve().parent / 'assets' / 'watcher.glb'))
rig = next(obj for obj in scene.objects if obj.type == 'ARMATURE')
root = rig
while root.parent:
    root = root.parent
body = bpy.data.objects['SuperHero_Male']
cloth = material('Watcher · painted knit and canvas', (.55, .15, .057))
colors = body.data.color_attributes.new(name='Costume', type='FLOAT_COLOR', domain='POINT')
for vertex, color in zip(body.data.vertices, colors.data):
    x, y, z = vertex.co
    if z > 1.54 and abs(x) < .15:
        shade = (.045, .027, .02) if z > 1.781 or (z > 1.687 and y > .04) else (.56, .315, .19)
    elif abs(x) > .44 and z > 1.04:
        shade = (.56, .315, .19)
    elif z > .995:
        shade = (.69, .148, .054)
    elif z > .12:
        shade = (.065, .151, .162)
    else:
        shade = (.062, .044, .033)
    color.color = (*shade, 1)
attr = cloth.node_tree.nodes.new('ShaderNodeVertexColor')
attr.layer_name = colors.name
cloth.node_tree.links.new(attr.outputs['Color'],
                          cloth.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.clear()
body.data.materials.append(cloth)
brows = bpy.data.objects['Eyebrows']
brows.data.materials.clear()
brows.data.materials.append(material('Brows', (.045, .023, .016)))

anim = rig.animation_data
for track in anim.nla_tracks:
    track.mute = track.name != 'Idle_relaxed'
strip = anim.nla_tracks['Idle_relaxed'].strips[0]
start, end = strip.frame_start, strip.frame_end
# Sample the clip before replacing its moving lower body with one planted pose.
bones = list(rig.pose.bones)
samples = []
for i in range(48):
    time = start + (end - start) * (.07 + .89 * i / 47)
    scene.frame_set(int(time), subframe=time % 1)
    samples.append([bone.matrix_basis.copy() for bone in bones])
rig.animation_data_clear()
head = rig.pose.bones['Head']
root.location = (-2.66, -3.20, .32)
root.rotation_mode = 'XYZ'
root.rotation_euler.z = radians(143)
for i, sample in enumerate(samples):
    for j, bone in enumerate(bones):
        moving = bone.name.startswith(('spine', 'neck', 'Head', 'clavicle', 'upperarm',
                                       'lowerarm', 'hand', 'thumb', 'index', 'middle', 'ring', 'pinky'))
        bone.matrix_basis = sample[j] if moving else samples[0][j]
    bpy.context.view_layer.update()
    # Track the amber leaf with the head, using the model's -Y forward axis.
    leaf_x = -2.65 + .099 * i
    eye = root.matrix_world @ (head.head + Vector((0, -.047, .13)))
    direction = Vector((leaf_x, -.91 + .09 * sin(i*.12), .05)) - eye
    local = root.matrix_world.to_3x3().inverted() @ direction
    yaw = atan2(local.x, -local.y)
    pitch = atan2(-local.z, hypot(local.x, local.y)) * .74
    turn = Quaternion((0, 0, 1), yaw) @ Quaternion((1, 0, 0), pitch)
    pose = (turn.to_matrix() @ head.bone.matrix_local.to_3x3()).to_4x4()
    pose.translation = head.head
    head.matrix = pose
    for bone in bones:
        bone.keyframe_insert(data_path='location', frame=i+1, group=bone.name)
        path = 'rotation_quaternion' if bone.rotation_mode == 'QUATERNION' else 'rotation_euler'
        bone.keyframe_insert(data_path=path, frame=i+1, group=bone.name)
        bone.keyframe_insert(data_path='scale', frame=i+1, group=bone.name)

scene.frame_set(1)
evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
sole = min((evaluated.matrix_world @ v.co).z for v in evaluated.data.vertices)
root.location.z += .322 - sole

bpy.ops.object.camera_add(location=(5.38, -10.45, 7.4))
camera = bpy.context.object
camera.name = 'Camera · river study'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 10.7
aim(camera, (-.42, -.10, .39))
scene.camera = camera

world = bpy.data.worlds.new('Soft blue sky')
scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.45, .60, .72, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .32

bpy.ops.object.light_add(type='SUN', location=(-5, -3, 8))
sun = bpy.context.object
sun.name = 'Late afternoon sun'
sun.data.energy = 2.15
sun.data.angle = .14
sun.data.color = (1, .845, .68)
aim(sun, (0, 0, 0))

bpy.ops.object.light_add(type='AREA', location=(1, 3, 6))
fill = bpy.context.object
fill.name = 'Cool skylight'
fill.data.energy = 460
fill.data.shape = 'DISK'
fill.data.size = 10
fill.data.color = (.65, .82, 1)
aim(fill, (0, -1, 0))
scene.frame_set(1)
assert scene.camera and rig.animation_data.action and scene.frame_end == 48
