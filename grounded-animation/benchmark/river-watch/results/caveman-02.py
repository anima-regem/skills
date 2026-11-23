"""Build a four-second riverbank scene in Blender."""
import math
import random

import bpy
from mathutils import Vector

random.seed(17)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'


def material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return mat


def mesh(name, vertices, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def oval(name, pos, scale, mat, facets=False):
    if facets:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, location=pos)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = not facets
    return obj


def limb(name, a, b, width, depth, mat):
    direction = Vector(b) - Vector(a)
    obj = oval(name, (Vector(a) + Vector(b)) / 2,
               (width, depth, direction.length / 2 + width * .6), mat)
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return obj


def center(y):
    return .48 * math.sin(y * .39) + .12 * math.sin(y * .83)


def half_width(y):
    return 2.08 + .19 * math.sin(y * .7 + 1.6)


def edge(y, side):
    return center(y) + side * half_width(y)


def strip(name, profile, mat):
    verts = [(x, y, z) for i in range(241) for y in [-24 + i * .2]
             for x, z in profile(y)]
    columns = len(profile(0))
    faces = [(i, i + 1, i + columns + 1, i + columns)
             for i in range(len(verts) - columns) if i % columns < columns - 1]
    return mesh(name, verts, faces, mat)


grass = material('Meadow • muted sage', (.205, .28, .115))
soil = material('Shore • warm silt', (.32, .23, .126))
wet = material('Shore • wet pebbles', (.17, .155, .095))
rock = [material('River stone', col) for col in
        [(.25, .29, .25), (.35, .36, .27), (.17, .23, .22), (.43, .37, .25)]]
blades = [material('Grass', col) for col in
          [(.28, .37, .10), (.36, .40, .145), (.16, .25, .095)]]

for side in (-1, 1):
    for label, near, far, z1, z2, mat in [
        ('Wet shelf', -.23, .10, -.09, .045, wet),
        ('Exposed silt', .10, .43, .045, .29, soil),
        ('Meadow', .43, 25, .29, .30, grass),
    ]:
        def profile(y):
            x = edge(y, side)
            h = .025 * math.sin(y * 2.4)
            points = [(x + side * near, z1 + h), (x + side * far, z2 + h)]
            return sorted(points)
        strip(label, profile, mat)

water = material('River • moving jade', (.035, .27, .28), .29)
nodes = water.node_tree.nodes
links = water.node_tree.links
coords = nodes.new('ShaderNodeTexCoord')
mapping = nodes.new('ShaderNodeVectorMath')
mapping.operation = 'MULTIPLY'
mapping.inputs[1].default_value = (2.45, .43, 1)
links.new(coords.outputs['Object'], mapping.inputs[0])
offset = nodes.new('ShaderNodeVectorMath')
offset.operation = 'ADD'
links.new(mapping.outputs[0], offset.inputs[0])
offset.inputs[1].driver_add('default_value', 1).driver.expression = '-(frame-1)*0.067'
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 2.2
noise.inputs['Detail'].default_value = 2
links.new(offset.outputs[0], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .17
ramp.color_ramp.elements[0].color = (.018, .145, .177, 1)
ramp.color_ramp.elements[1].position = .83
ramp.color_ramp.elements[1].color = (.088, .39, .355, 1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
shader = nodes.get('Principled BSDF')
links.new(ramp.outputs[0], shader.inputs['Base Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .24
bump.inputs['Distance'].default_value = .065
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs['Normal'], shader.inputs['Normal'])
strip('Flowing channel', lambda y: [(edge(y, -1) - .13, 0),
                                   (edge(y, 1) + .13, 0)], water)

foam = [material('Current glint', col, .37) for col in
        [(.09, .39, .36), (.17, .49, .44), (.29, .61, .54), (.47, .72, .60)]]


def ribbon(name, length, width, mat):
    verts = []
    for i in range(13):
        t = i / 12
        x = .032 * math.sin(t * math.tau)
        spread = .5 * width * math.sin(math.pi * t) ** .7
        verts.extend([(x - spread, length * t, 0), (x + spread, length * t, 0)])
    return mesh(name, verts, [(i, i+1, i+3, i+2) for i in range(0, 24, 2)], mat)


def carry(obj, start, lane, speed, height):
    # Sample the channel curve so each mark follows its own streamline.
    for frame in [1, 7, 13, 19, 25, 31, 37, 43, 48]:
        y = start + (frame - 1) * speed / 12
        x = center(y) + lane * half_width(y)
        obj.location = (x, y, height)
        obj.rotation_euler.z = -math.atan2(
            center(y + .3) - center(y) + lane * (half_width(y + .3) - half_width(y)), .3)
        obj.keyframe_insert('location', frame=frame)
        obj.keyframe_insert('rotation_euler', frame=frame)
    action = obj.animation_data.action
    for curve in action.layers[0].strips[0].channelbag(obj.animation_data.action_slot).fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'


for i in range(145):
    lane = random.uniform(-.94, .94)
    streak = ribbon('Drifting surface streak', random.uniform(.17, .90),
                    random.uniform(.014, .052), random.choices(foam, (5, 4, 2, 1))[0])
    carry(streak, random.uniform(-19, 15), lane, 2.13 - .93 * abs(lane) ** 2, .012)

leaves = [material('Floating leaf', (.58, .22, .043)),
          material('Floating leaf', (.69, .39, .071))]
for i, (y, lane) in enumerate([(-7.4, -.5), (-4.4, -.30), (-1.9, .43), (1.4, -.12)]):
    leaf = oval('Leaf carried downstream', (0, 0, 0), (.055, .125, .018), leaves[i % 2])
    carry(leaf, y, lane, 2.05 - .9 * lane**2, .033)

for side in (-1, 1):
    for i in range(64):
        y = random.uniform(-13, 13)
        d = random.uniform(-.23, 1.15)
        size = random.uniform(.045, .19) * (1.4 if d > .4 else 1)
        z = max(-.07, min(.27, (d - .10) * .74))
        stone = oval('Bank cobble', (edge(y, side) + side*d, y, z),
                     (size, size * random.uniform(.7, 1.65), size * .64),
                     random.choice(rock), True)
        stone.rotation_euler.z = random.uniform(0, math.tau)

for x, y, scale in [(-1.30, 1.65, .29), (1.16, -1.70, .24), (1.49, 3.61, .35)]:
    stone = oval('Emergent river stone', (x, y, -.035),
                 (scale, scale * .79, scale * .86), rock[2], True)
    stone.rotation_euler.z = .48
    for side in (-1, 1):
        for i in range(3):
            wake = ribbon('Stream around stone', .36 + .10*i, .038, foam[2-i//2])
            wake.location = (x + side * (scale*.91 + .065*i), y - .19 + .26*i, .018)
            wake.rotation_euler.z = side * (.28*i - .33)
            for frame, phase in [(1, 0), (13, 1), (25, 0), (37, 1), (48, 0)]:
                wake.scale.y = 1 + .29 * phase
                wake.keyframe_insert('scale', frame=frame)


def tuft(x, y, size):
    verts, faces = [], []
    for _ in range(random.randint(4, 8)):
        a = random.uniform(0, math.tau)
        u, v = math.cos(a), math.sin(a)
        h = size * random.uniform(.5, 1.15)
        w = h * random.uniform(.055, .11)
        dx, dy = x + u * size*.19, y + v * size*.19
        k = len(verts)
        verts.extend([(dx-v*w, dy+u*w, .29), (dx+v*w, dy-u*w, .29),
                      (dx+u*h*.24+v*w*.55, dy+v*h*.24-u*w*.55, .29+h*.65),
                      (dx+u*h*.64, dy+v*h*.64, .29+h),
                      (dx+u*h*.24-v*w*.55, dy+v*h*.24+u*w*.55, .29+h*.65)])
        faces.extend([(k,k+1,k+2,k+4), (k+4,k+2,k+3)])
    mesh('Meadow tuft', verts, faces, random.choice(blades))


for side in (-1, 1):
    for i in range(145):
        y = random.uniform(-15, 15)
        d = random.uniform(.48, 3.3)
        if side == -1 and abs(y + .6) < .65 and d < 1.18:
            continue
        tuft(edge(y, side) + side*d, y, random.uniform(.12, .39))


# The character is modeled in local coordinates with +X forward.
jacket = material('Ochre canvas', (.67, .255, .043))
seam = material('Canvas seams', (.36, .105, .025))
pants = material('Slate trousers', (.045, .104, .118))
boot = material('Dark leather', (.062, .039, .025))
sole = material('Boot soles', (.029, .023, .019))
skin = material('Warm complexion', (.5, .245, .138))
hair = material('Dark hair and pupils', (.050, .024, .016))
hat = material('Petrol knit cap', (.036, .17, .169))
hat_band = material('Petrol knit cuff', (.024, .091, .098))
eye = material('Eye whites', (.73, .65, .48))


def empty(name, location, parent=None):
    obj = bpy.data.objects.new(name, None)
    scene.collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    return obj


root = empty('Watcher • planted on left bank', (edge(-.65, -1)-.76, -.65, .305))
root.rotation_euler.z = .14


def part(name, xyz, size, mat, parent=root):
    obj = oval(name, xyz, size, mat)
    obj.parent = parent
    return obj


def segment(name, a, b, width, depth, mat, parent=root):
    obj = limb(name, a, b, width, depth, mat)
    obj.parent = parent
    return obj


for side in (-1, 1):
    y = side * .127
    x = .065 * side
    part('Boot sole', (x+.062,y,.051), (.184,.102,.040), sole)
    part('Hiking boot', (x+.047,y,.109), (.165,.095,.082), boot)
    segment('Trouser shin', (x-.025,y,.16), (.035,y,.47), .094,.100,pants)
    segment('Trouser thigh', (.035,y,.47), (-.02,y*.82,.82), .119,.115,pants)
part('Hips', (-.022,0,.803), (.172,.220,.157), pants)

torso = empty('Breathing pivot', (-.025,0,.82), root)
part('Canvas jacket', (0,0,.229), (.207,.258,.343), jacket, torso)
part('Jacket hem', (0,0,.014), (.191,.237,.086), seam, torso)
part('Jacket collar', (.028,0,.483), (.132,.161,.098), seam, torso)
segment('Front placket', (.192,0,.062), (.197,0,.417), .014,.019,seam,torso)
for side in (-1, 1):
    shoulder = (-.025, side*.236,.398)
    elbow = (-.063, side*.279,.235)
    hand = (.115, side*.210,.137)
    segment('Upper sleeve', shoulder, elbow, .097,.099,jacket,torso)
    segment('Bent sleeve', elbow, hand, .080,.083,jacket,torso)
    part('Hand at pocket', hand, (.069,.064,.058), skin,torso)
    segment('Pocket welt', (.144,side*.18,.109), (.158,side*.203,.188),
            .017,.022,seam,torso)

part('Neck', (.034,0,.514), (.085,.094,.126), skin,torso)
head = empty('Gaze follows the current', (.048,0,.549), torso)
part('Head', (.011,0,.136), (.137,.126,.171), skin,head)
part('Jaw', (.042,0,.069), (.112,.106,.086), skin,head)
part('Nose', (.146,0,.126), (.051,.036,.038), skin,head)
part('Hair at nape', (-.064,0,.171), (.085,.125,.117), hair,head)
for side in (-1, 1):
    part('Ear', (-.013,side*.119,.126), (.038,.027,.047), skin,head)
    eye_piece = part('Eye', (.113,side*.061,.157), (.023,.025,.014), eye,head)
    eye_piece.rotation_euler.z = side*.52
    part('Pupil', (.133,side*.066,.157), (.011,.010,.011), hair,head)
    part('Brow', (.115,side*.061,.181), (.018,.026,.008), hair,head)
part('Knit cap', (-.022,0,.246), (.147,.138,.112), hat,head)
part('Folded cap cuff', (-.014,0,.211), (.154,.143,.045), hat_band,head)
part('Cap crown', (-.063,0,.338), (.065,.067,.044), hat,head)

for frame, turn, tilt, lean in [(1,-25,13,4), (10,-21,16,5), (30,23,14,7),
                                 (40,29,9,5), (48,19,12,4)]:
    head.rotation_euler = (0, math.radians(tilt), math.radians(turn))
    torso.rotation_euler.y = math.radians(lean)
    head.keyframe_insert('rotation_euler', frame=frame)
    torso.keyframe_insert('rotation_euler', frame=frame)


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()


bpy.ops.object.camera_add(location=(7.0,-11.0,10.2))
camera = bpy.context.object
camera.name = 'Riverbank composition'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 11.0
aim(camera, (-.26,.25,.15))
scene.camera = camera

world = bpy.data.worlds.new('Cool open air')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.46,.59,.73,1)
world.node_tree.nodes['Background'].inputs[1].default_value = .43
scene.world = world

bpy.ops.object.light_add(type='SUN', location=(-5,-4,8))
sun = bpy.context.object
sun.name = 'Low afternoon sun'
sun.data.energy = 2.6
sun.data.angle = .14
sun.data.color = (1,.83,.65)
aim(sun, (0,0,0))

bpy.ops.object.light_add(type='AREA', location=(3,1,7))
fill = bpy.context.object
fill.name = 'Broad skylight'
fill.data.energy = 330
fill.data.shape = 'DISK'
fill.data.size = 8
fill.data.color = (.65,.83,1)
aim(fill,(0,0,0))

scene.frame_set(1)
