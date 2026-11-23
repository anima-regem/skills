"""Build the entire shot in Blender background mode.

watcher.glb combines KinemIQ_Mannequin.glb and GLB/Idle_relaxed.glb,
by KinemIQ, CC0 v1.0:
https://github.com/Kinemiq/free-game-animations/releases/tag/v1.0
"""
from math import cos, exp, pi, radians, sin
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
scene.world = bpy.data.worlds.new("Blue sky fill")
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.42, .60, .75, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .36
scene.view_settings.view_transform = 'AgX'
rng = Random(31)


def material(name, rgb, roughness=.82, emission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*rgb, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Emission Color'].default_value = (*rgb, 1)
    shader.inputs['Emission Strength'].default_value = emission
    return mat


def mesh_object(name, vertices, faces, materials):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    for mat in materials:
        mesh.materials.append(mat)
    return obj


bpy.ops.import_scene.gltf(filepath=str(Path(__file__).resolve().parent / 'assets' / 'watcher.glb'))
rig = bpy.data.objects['Armature']
root = bpy.data.objects['KinemIQ_Mannequin']
anim = rig.animation_data
idle = bpy.data.actions['Idle_relaxed']
for track in list(anim.nla_tracks):
    anim.nla_tracks.remove(track)
anim.action = idle
anim.action_slot = idle.slots[0]

coat = material("Persimmon canvas", (.64, .102, .033))
pants = material("Deep spruce trousers", (.025, .093, .106))
boots = material("Dark leather", (.041, .028, .024))
skin = material("Warm ochre skin", (.52, .263, .134))
hair = material("Dark umber hair", (.049, .021, .014))
eye = material("Dark eyes", (.027, .019, .015))
collar = material("Shearling collar", (.77, .47, .23))

body = bpy.data.objects['SuperHero_Male']
for mat in (coat, pants, boots, skin, hair, collar):
    body.data.materials.append(mat)
for face in body.data.polygons:
    center = sum((body.data.vertices[i].co for i in face.vertices), Vector()) / len(face.vertices)
    x, y, z = center
    if z > 1.531:
        index = 5 if z > 1.694 + .32 * max(0, -y - .10) or (y > -.066 and z > 1.60) else 4
    elif z > 1.467 and abs(x) < .112:
        index = 6
    elif abs(x) > .285 and .80 < z < 1.006:
        index = 4
    elif z > .945 or (abs(x) > .247 and z > 1.00):
        index = 1
    elif z > .145:
        index = 2
    else:
        index = 3
    face.material_index = index
    face.use_smooth = True
bpy.data.objects['Eyebrows'].data.materials[0] = hair
bpy.data.objects['Eyes'].data.materials[0] = eye

# Sample and retime the imported performance. Add a glance in armature space,
# converting its axes to the posed head's own rotation space on each sample.
head = rig.pose.bones['Head']
samples = []
for frame in range(1, 49):
    t = (frame - 1) / 47
    source = 29 * t
    scene.frame_set(int(source), subframe=source % 1)
    channels = [(b, b.location.copy(), b.rotation_quaternion.copy(), b.scale.copy())
                for b in rig.pose.bones]
    yaw = radians(-18 + 57 * (.5 - .5 * cos(pi * t)))
    pitch = radians(15 + 5 * exp(-((t - .32) / .24) ** 2))
    rotation = Quaternion((0, 0, 1), -yaw) @ Quaternion((1, 0, 0), pitch)
    basis = head.matrix.to_quaternion()
    samples.append((frame, channels, basis.inverted() @ rotation @ basis))

anim.action = None
for frame, channels, glance in samples:
    for bone, location, rotation, scale in channels:
        bone.location, bone.scale = location, scale
        bone.rotation_quaternion = rotation @ glance if bone == head else rotation
        for path in ('location', 'rotation_quaternion', 'scale'):
            bone.keyframe_insert(path, frame=frame, group=bone.name)
anim.action.name = "Relaxed stance with downstream glance"

# X increases downstream. Both shore meshes share the same channel profile.
def centerline(x):
    return .39 * sin(.34 * x + .3) + .13 * sin(.82 * x)


def half_width(x):
    return 1.98 + .22 * cos(.37 * x - .25)


def shore(x, side):
    return centerline(x) + side * half_width(x)


def bank_height(x, distance):
    return .44 + (1 - exp(-max(distance, 0) * 1.3)) * (
        .12 + .047 * cos(x * .9) + .04 * sin(distance * 1.3))


grass = material("Dry meadow", (.22, .26, .105))
grass_nodes = grass.node_tree.nodes
grass_links = grass.node_tree.links
grass_coords = grass_nodes.new('ShaderNodeTexCoord')
grass_noise = grass_nodes.new('ShaderNodeTexNoise')
grass_noise.inputs['Scale'].default_value = 1.25
grass_noise.inputs['Detail'].default_value = 2
grass_ramp = grass_nodes.new('ShaderNodeValToRGB')
for stop, position, rgb in zip(grass_ramp.color_ramp.elements, (.18, .84),
                               ((.16, .215, .075), (.29, .31, .13))):
    stop.position = position
    stop.color = (*rgb, 1)
grass_links.new(grass_coords.outputs['Object'], grass_noise.inputs['Vector'])
grass_links.new(grass_noise.outputs['Fac'], grass_ramp.inputs[0])
grass_links.new(grass_ramp.outputs[0], grass_nodes['Principled BSDF'].inputs['Base Color'])
soil = [material("Sediment", (.29, .205, .112)),
        material("Wet sediment", (.14, .115, .077)),
        material("Sand lip", (.39, .294, .155))]

for side in (-1, 1):
    vertices, faces = [], []
    distances = (-.34, -.12, .12, .29, .53, .86, 1.27, 1.9, 2.8, 4.1, 6.1, 9, 14)
    for i in range(161):
        x = (i - 80) * .24
        for distance in distances:
            z = bank_height(x, distance) if distance >= .29 else {
                -.34: -.12, -.12: .045, .12: .245}[distance]
            if distance < .53:
                z += .022 * sin(2.8 * x + side)
            vertices.append((x, shore(x, side) + side * distance, z))
    width = len(distances)
    for i in range(160):
        for j in range(width - 1):
            a = i * width + j
            quad = (a, a + width, a + width + 1, a + 1)
            faces.append(quad if side == 1 else quad[::-1])
    bank = mesh_object("Near meadow bank" if side == -1 else "Far meadow bank",
                       vertices, faces, [grass] + soil)
    for face in bank.data.polygons:
        j = face.index % (width - 1)
        face.material_index = (2, 1, 3)[j] if j < 3 else 0
        face.use_smooth = True

person_x = -2.65
person_distance = .61
root.location = (person_x, shore(person_x, -1) - person_distance,
                 bank_height(person_x, person_distance))
root.rotation_mode = 'XYZ'
root.rotation_euler.z = radians(174)

water = material("River | moving surface", (.024, .239, .266), .31, .16)
nodes, links = water.node_tree.nodes, water.node_tree.links
shader = nodes['Principled BSDF']
coords = nodes.new('ShaderNodeTexCoord')
mapping = nodes.new('ShaderNodeMapping')
mapping.inputs['Scale'].default_value = (.68, 4.4, 1)
links.new(coords.outputs['Object'], mapping.inputs[0])
for frame, offset in ((1, 0), (48, -3.9)):
    mapping.inputs['Location'].default_value.x = offset
    mapping.inputs['Location'].keyframe_insert('default_value', index=0, frame=frame)
for channel in water.node_tree.animation_data.action.layers[0].strips[0].channelbag(
        water.node_tree.animation_data.action_slot).fcurves:
    for key in channel.keyframe_points:
        key.interpolation = 'LINEAR'
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.6
noise.inputs['Detail'].default_value = 2.4
links.new(mapping.outputs[0], noise.inputs[0])
ramp = nodes.new('ShaderNodeValToRGB')
for element, position, color in zip(
        [ramp.color_ramp.elements[0], ramp.color_ramp.elements.new(.53),
         ramp.color_ramp.elements.new(.73), ramp.color_ramp.elements[-1]],
        [.22, .53, .73, .9],
        [(.017, .136, .168), (.031, .275, .285), (.106, .402, .395), (.34, .56, .49)]):
    element.position, element.color = position, (*color, 1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
links.new(ramp.outputs[0], shader.inputs['Base Color'])
links.new(ramp.outputs[0], shader.inputs['Emission Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .19
bump.inputs['Distance'].default_value = .036
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs[0], shader.inputs['Normal'])
mesh_object("River surface", [(-20, -3.4, .088), (20, -3.4, .088),
                             (20, 3.4, .088), (-20, 3.4, .088)],
            [(0, 1, 2, 3)], [water])

foam = [material("Water glint", (.30, .62, .59), .44, .26),
        material("Pale swirls", (.65, .83, .74), .5, .30),
        material("Muted current", (.13, .40, .40), .37, .20)]


def stroke(x, y, length, width, bend, z=.099):
    vertices = []
    for i in range(13):
        t = i / 12
        offset = bend * sin(t * pi)
        radius = width * (.05 + .95 * sin(pi * t) ** .75)
        vertices.extend(((x + length * t, y + offset - radius, z),
                         (x + length * t, y + offset + radius, z)))
    return vertices, [(j, j + 2, j + 3, j + 1) for j in range(0, 24, 2)]


# Narrow glints and longer pale rafts move together through the channel.
for i in range(132):
    x = rng.uniform(-18, 12)
    lane = rng.uniform(-.88, .88)
    length = rng.uniform(.15, .88) * (1.5 if i % 8 == 0 else 1)
    vertices, faces = stroke(-length / 2, 0, length, rng.uniform(.008, .029),
                             rng.uniform(-.033, .033))
    mark = mesh_object("Drifting surface glint", vertices, faces, foam)
    for face in mark.data.polygons:
        face.material_index = [0, 2, 2, 0, 2, 1, 0, 2][i % 8]
    speed = (.82 + .66 * (1 - lane**2)) * rng.uniform(.8, 1.1)
    for frame in (1, 13, 25, 37, 48):
        travel_x = x + speed * (frame - 1) / 12
        mark.location = (travel_x, centerline(travel_x) + lane * half_width(travel_x), 0)
        mark.keyframe_insert('location', frame=frame)

stone = [material("Shale", (.17, .185, .168)), material("Pale shale", (.32, .307, .234)),
         material("Mossy shale", (.195, .233, .111))]


def rock(x, y, z, scale, mat, detail=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=detail, radius=1, location=(x, y, z))
    obj = bpy.context.object
    obj.name = "River stone"
    obj.scale = scale
    obj.rotation_euler.z = rng.uniform(-pi, pi)
    for vert in obj.data.vertices:
        vert.co *= rng.uniform(.84, 1.14)
    obj.data.materials.append(mat)
    return obj


for x, y, size in ((.80, -.70, .31), (1.21, -.49, .21), (-4.55, 1.27, .28)):
    rock(x, y, .09, (size * 1.25, size, size * .7), stone[0], 2)
    for side in (-1, 1):
        for j in range(3):
            vertices, faces = stroke(x - .20 + .18 * j, y + side * size * (.81 + .4 * j),
                                     1.15 + j * .36, .015, side * (.11 + j * .045))
            mesh_object("Water curling around stone", vertices, faces, [foam[j % 3]])

for i in range(77):
    x = rng.uniform(-12, 12)
    side = rng.choice((-1, 1))
    distance = rng.uniform(-.03, 1.5)
    y = shore(x, side) + side * distance
    if (Vector((x, y)) - root.location.xy).length < .46:
        continue
    z = bank_height(x, distance) if distance >= .29 else .15 + distance
    size = rng.uniform(.035, .17)
    rock(x, y, z - .02, (size * 1.4, size, size * .66), rng.choice(stone))

blades = [material("Reed olive", (.27, .31, .091)), material("Reed amber", (.45, .37, .105)),
          material("Reed tips", (.57, .46, .182))]
vertices, faces, colors = [], [], []
for i in range(122):
    x = rng.uniform(-13, 13)
    side = rng.choice((-1, 1))
    distance = rng.uniform(.32, 2.8)
    y = shore(x, side) + side * distance
    if (Vector((x, y)) - root.location.xy).length < .56:
        continue
    z = bank_height(x, distance) - .022
    height = rng.uniform(.105, .34)
    for j in range(rng.randrange(4, 9)):
        angle = rng.uniform(0, 2 * pi)
        dx, dy = cos(angle), sin(angle)
        h = height * rng.uniform(.5, 1.31)
        w = rng.uniform(.011, .025)
        px, py = x + dx * .055, y + dy * .055
        a = len(vertices)
        vertices += [(px - dy*w, py + dx*w, z), (px + dy*w, py - dx*w, z),
                     (px + dx*h*.23 + dy*w*.6, py + dy*h*.23 - dx*w*.6, z + h*.56),
                     (px + dx*h*.23 - dy*w*.6, py + dy*h*.23 + dx*w*.6, z + h*.56),
                     (px + dx*h*.52, py + dy*h*.52, z + h)]
        faces += [(a, a+1, a+2, a+3), (a+3, a+2, a+4)]
        color = rng.randrange(2)
        colors.extend((color, rng.choice((color, color, 2))))
meadow = mesh_object("Riverside grasses", vertices, faces, blades)
for face, color in zip(meadow.data.polygons, colors):
    face.material_index = color


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


camera_data = bpy.data.cameras.new("Riverside camera")
camera = bpy.data.objects.new("Riverside camera", camera_data)
scene.collection.objects.link(camera)
camera.location = (3.65, -9.4, 7.8)
aim(camera, (-.45, -.44, .18))
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 10.65
scene.camera = camera

sun_data = bpy.data.lights.new("Late sun", 'SUN')
sun_data.energy = 2.25
sun_data.angle = radians(9)
sun_data.color = (1, .84, .66)
sun = bpy.data.objects.new("Late sun", sun_data)
scene.collection.objects.link(sun)
sun.location = (-4, -1.5, 7)
aim(sun, (0, 0, 0))

fill_data = bpy.data.lights.new("Skylight", 'AREA')
fill_data.energy = 320
fill_data.shape = 'DISK'
fill_data.size = 9
fill_data.color = (.68, .86, 1)
fill = bpy.data.objects.new("Skylight", fill_data)
scene.collection.objects.link(fill)
fill.location = (2, 2, 6)
aim(fill, (0, 0, 0))

scene.frame_set(1)
