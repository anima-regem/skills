import math
import random

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'
rng = random.Random(17)


def material(name, rgb, roughness=.8):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*rgb, 1)
    shader.inputs['Roughness'].default_value = roughness
    return mat


def mesh(name, vertices, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    data.materials.append(mat)
    return obj


def oval(name, center, scale, mat, parent=None, faceted=False):
    if faceted:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12)
    obj = bpy.context.object
    obj.name, obj.parent, obj.location, obj.scale = name, parent, center, scale
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = not faceted
    return obj


def limb(name, start, end, width, depth, mat, parent):
    axis = Vector(end) - Vector(start)
    obj = oval(name, Vector(start) + axis / 2, (width, depth, axis.length / 2 + width * .48), mat, parent)
    obj.rotation_euler = axis.to_track_quat('Z', 'Y').to_euler()
    return obj


grass = material('Sage meadow', (.28, .36, .19))
verge = material('Ochre gravel', (.42, .34, .21))
earth = material('Dark wet stone', (.17, .18, .13))
rocks = [material('Slate', (.24, .29, .28)), material('Warm gray stone', (.38, .36, .29))]
water = material('River turquoise', (.045, .30, .32), .32)
foam = [material('Pale broken reflections', (.40, .73, .67), .52),
        material('Soft broken reflections', (.18, .49, .47), .48)]
greens = [material('Rush tips', (.40, .44, .20)), material('Rush shadows', (.17, .26, .13))]
pine = [material('Pine shadow', (.09, .20, .16)), material('Pine sun', (.18, .31, .21))]


def centerline(x):
    return .40 * math.sin(x * .31) + .16 * math.sin(x * .65)


def edge(x, side):
    return centerline(x) + side * (2.22 + .11 * math.sin(x * 1.25 + side))


def strip(name, y_a, z_a, y_b, z_b, mat):
    vertices = [(x, y(x), z) for i in range(145) for x in [-36 + i * .5]
                for y, z in [(y_a, z_a), (y_b, z_b)]]
    faces = [(i, i+2, i+3, i+1) for i in range(0, len(vertices)-2, 2)]
    if vertices[0][1] > vertices[1][1]:
        faces = [face[::-1] for face in faces]
    return mesh(name, vertices, faces, mat)


strip('River surface', lambda x: -5, 0, lambda x: 5, 0, water)
for side in (-1, 1):
    def shore(x):
        return edge(x, side)

    def gravel(x):
        return shore(x) + side * (.23 + .08 * math.sin(x * 2.4))

    def meadow(x):
        return gravel(x) + side * (.57 + .12 * math.sin(x * .85))

    strip('Wet shoreline', shore, -.035, gravel, .19, earth)
    strip('Gravel shelf', gravel, .19, meadow, .33, verge)
    strip('Meadow', meadow, .33, lambda x: side * 25, .33, grass)

nodes = water.node_tree.nodes
links = water.node_tree.links
coords = nodes.new('ShaderNodeTexCoord')
stretch = nodes.new('ShaderNodeVectorMath')
stretch.operation = 'MULTIPLY'
stretch.inputs[1].default_value = (.37, 2.4, 1)
links.new(coords.outputs['Object'], stretch.inputs[0])
shift = nodes.new('ShaderNodeVectorMath')
shift.operation = 'ADD'
links.new(stretch.outputs[0], shift.inputs[0])
for frame in (1, 48):
    shift.inputs[1].default_value = (-.37 * (frame - 1) * .093, 0, 0)
    shift.inputs[1].keyframe_insert(data_path='default_value', frame=frame)
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.15
noise.inputs['Detail'].default_value = 2
links.new(shift.outputs[0], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .18
ramp.color_ramp.elements[0].color = (.025, .19, .23, 1)
ramp.color_ramp.elements[1].position = .84
ramp.color_ramp.elements[1].color = (.085, .38, .38, 1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
links.new(ramp.outputs[0], nodes.get('Principled BSDF').inputs['Base Color'])

# The tapered surface marks drift downstream faster in the middle of the channel.
for i in range(99):
    x = rng.uniform(-18, 16)
    lane = rng.uniform(-.91, .91)
    length = rng.uniform(.16, .93)
    width = rng.uniform(.013, .041)
    fleck = mesh('Current glint',
                 [(-length*.53, -.009, 0), (-length*.17, width*.55, 0),
                  (length*.26, width*.42, 0), (length*.47, .008, 0),
                  (length*.12, -width*.55, 0), (-length*.26, -width*.37, 0)],
                 [(5, 4, 3, 2, 1, 0)], rng.choice(foam))
    speed = .063 + .055 * (1 - lane ** 2)
    for frame in (1, 12, 24, 36, 48):
        travel = x + (frame - 1) * speed
        fleck.location = (travel, centerline(travel) + lane * 2.21, .014)
        fleck.keyframe_insert(data_path='location', frame=frame)
    for curve in fleck.animation_data.action.layers[0].strips[0].channelbag(
            fleck.animation_data.action_slot).fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'

for side in (-1, 1):
    for i in range(46):
        x = rng.uniform(-14, 13)
        y = edge(x, side) + side * rng.uniform(.12, 1.35)
        size = rng.uniform(.045, .22)
        obj = oval('Bank pebble', (x, y, .19 if abs(y-edge(x, side)) < .38 else .31),
                   (size*1.35, size, size*.58), rng.choice(rocks), faceted=True)
        obj.rotation_euler.z = rng.uniform(0, math.tau)

    for i in range(27):
        x = rng.uniform(-14, 13)
        y = edge(x, side) + side * rng.uniform(.68, 1.8)
        verts, faces = [], []
        for blade in range(7):
            px, py = x + rng.uniform(-.11, .11), y + rng.uniform(-.10, .10)
            h = rng.uniform(.11, .38)
            bend = rng.uniform(-.14, .14)
            base = len(verts)
            verts.extend([(px-.025, py, .29), (px+.025, py, .29),
                          (px+bend*.45+.015, py+.03, .29+h*.57),
                          (px+bend, py+.10, .29+h),
                          (px+bend*.45-.015, py+.03, .29+h*.57)])
            faces.extend([(base, base+1, base+2, base+4), (base+4, base+2, base+3)])
        mesh('Bank rushes', verts, faces, rng.choice(greens))

for x, y, size in [(-8, 5.6, 1.5), (-6.8, 6.5, 1.23), (-9, 7.5, 1.75),
                   (2.1, 4.10, 1.22), (3.5, 4.65, 1.67), (4.7, 4.35, 1.10),
                   (8.5, 7.4, 1.63), (10, 7.9, 1.24)]:
    oval('Pine trunk', (x, y, .63), (.10, .10, .45), earth, faceted=True)
    for tier in range(3):
        radius = size * (.46 - .083*tier)
        depth = size * .80
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=radius, radius2=.035, depth=depth,
                                        location=(x, y, .53 + depth/2 + tier*size*.32))
        bpy.context.object.name = 'Pine crown'
        bpy.context.object.rotation_euler.z = tier * .24
        bpy.context.object.data.materials.append(pine[tier % 2])

coat = material('Marigold canvas', (.74, .30, .045))
trim = material('Canvas seams', (.49, .155, .025))
pants = material('Indigo trousers', (.055, .10, .145))
boots = material('Umber boots', (.08, .045, .032))
skin = material('Warm clay complexion', (.53, .25, .13))
hat = material('Brick red wool', (.39, .065, .047))
eye = material('Dark eyes', (.036, .021, .017))


def pivot(name, location, parent=None):
    obj = bpy.data.objects.new(name, None)
    scene.collection.objects.link(obj)
    obj.parent, obj.location = parent, location
    return obj


person = pivot('River watcher', (-3.0, -3.63, .33))
person.rotation_euler.z = -.56
for side in (-1, 1):
    x = side * .118
    offset = side * .055
    limb('Trouser leg', (x, 0, .91), (x*1.20, offset, .21), .104, .109, pants, person)
    oval('Boot', (x*1.20, offset+.058, .095), (.111, .188, .096), boots, person)

body = pivot('Breathing pivot', (0, 0, .84), person)
oval('Jacket hem', (0, 0, .035), (.247, .165, .10), trim, body)
oval('Canvas jacket', (0, .012, .275), (.271, .182, .295), coat, body)
oval('Folded hood', (0, -.126, .48), (.214, .126, .143), trim, body)
for side in (-1, 1):
    shoulder = (side*.214, .003, .425)
    elbow = (side*.289, .030, .216)
    wrist = (side*.231, .126, .084)
    limb('Upper sleeve', shoulder, elbow, .104, .101, coat, body)
    limb('Lower sleeve', elbow, wrist, .088, .082, coat, body)
    oval('Cuff', wrist, (.071, .076, .058), trim, body)
    oval('Hand at pocket', (wrist[0], wrist[1]+.028, wrist[2]-.020), (.059, .064, .065), skin, body)

head = pivot('Head follows the current', (0, .036, .535), body)
oval('Neck', (0, .009, .04), (.084, .082, .101), skin, head)
oval('Face', (0, .027, .18), (.138, .126, .164), skin, head)
oval('Nose', (0, .151, .16), (.043, .061, .048), skin, head)
for side in (-1, 1):
    oval('Ear', (side*.127, .023, .161), (.033, .041, .051), skin, head)
    oval('Eye', (side*.063, .136, .197), (.019, .012, .014), eye, head)
oval('Wool cap', (0, .013, .273), (.151, .139, .116), hat, head)
oval('Turned cap brim', (0, .025, .248), (.155, .146, .040), hat, head)

for frame, lean, turn, pitch in [(1, -.029, .16, .15), (12, -.042, .13, .17),
                                  (31, -.071, -.37, .20), (48, -.032, -.48, .12)]:
    body.rotation_euler.x = lean
    body.keyframe_insert(data_path='rotation_euler', frame=frame)
    head.rotation_euler = (pitch, 0, turn)
    head.keyframe_insert(data_path='rotation_euler', frame=frame)

world = bpy.data.worlds.new('Soft daylight')
scene.world = world
world.node_tree.nodes['Background'].inputs[0].default_value = (.58, .71, .78, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .38

bpy.ops.object.light_add(type='SUN', location=(-5, -4, 8))
sun = bpy.context.object
sun.rotation_euler = Vector((.65, .28, -1)).to_track_quat('-Z', 'Y').to_euler()
sun.data.energy = 2.6
sun.data.color = (1, .83, .64)
sun.data.angle = math.radians(12)
bpy.ops.object.light_add(type='AREA', location=(1, 3, 7))
bpy.context.object.data.energy = 340
bpy.context.object.data.shape = 'DISK'
bpy.context.object.data.size = 8

bpy.ops.object.camera_add(location=(6, -14, 10))
camera = bpy.context.object
camera.rotation_euler = (Vector((-.28, .28, .20)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 12.6
scene.camera = camera
scene.frame_set(1)

first_glint = bpy.data.objects['Current glint']
start_x, start_turn = first_glint.location.x, head.rotation_euler.z
scene.frame_set(48)
assert first_glint.location.x > start_x and head.rotation_euler.z < start_turn
scene.frame_set(1)
