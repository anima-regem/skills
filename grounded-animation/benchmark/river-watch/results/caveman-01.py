"""A quiet riverbank, built procedurally for Blender 5.2."""
import math
import random

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
rng = random.Random(42)
sin, cos = math.sin, math.cos


def material(name, color, roughness=.75):
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
    data.materials.append(mat)
    return obj


def sphere(name, point, scale, mat, rock=False):
    if rock:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, location=point)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=point)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = not rock
    return obj


def limb(name, a, b, width, depth, mat):
    a, b = Vector(a), Vector(b)
    obj = sphere(name, (a+b)/2, (width, depth, (b-a).length/2 + width*.52), mat)
    obj.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return obj


grass = material('Sage meadow', (.30, .39, .22))
far_grass = material('Far meadow', (.37, .44, .26))
sand = material('Ochre gravel', (.47, .34, .18))
wet = material('Wet river silt', (.24, .25, .15))
stone = [material('River stone', c) for c in
         [(.19, .23, .22), (.29, .31, .25), (.37, .35, .28)]]
blades = [material('Rushes', c) for c in
          [(.15, .24, .12), (.33, .40, .15), (.51, .47, .21)]]
teal = material('River', (.045, .32, .34), .34)
foam = [material('Current glints', c, .42) for c in
        [(.095, .42, .44), (.20, .53, .51), (.45, .68, .61), (.64, .78, .68)]]


def center(x):
    return .43*sin(x*.46) + .15*sin(x*.89)


def edge(x, side):
    return center(x) + side*(2.12 + .17*cos(x*.69 + side))


def strip(name, rails, mat):
    vertices = [(x, y, z)
                for i in range(161)
                for x in [-24 + .3*i]
                for y, z in rails(x)]
    n = len(rails(0))
    faces = [(i*n+j, (i+1)*n+j, (i+1)*n+j+1, i*n+j+1)
             for i in range(160) for j in range(n-1)]
    return mesh(name, vertices, faces, mat)


river = strip('Continuous river surface', lambda x: [(edge(x, -1)-.11, 0),
                                                     (edge(x, 1)+.11, 0)], teal)
nodes = teal.node_tree.nodes
links = teal.node_tree.links
coords = nodes.new('ShaderNodeTexCoord')
stretch = nodes.new('ShaderNodeVectorMath')
stretch.operation = 'MULTIPLY'
stretch.inputs[1].default_value = (.41, 3.5, 1)
links.new(coords.outputs['Object'], stretch.inputs[0])
shift = nodes.new('ShaderNodeVectorMath')
shift.operation = 'ADD'
links.new(stretch.outputs[0], shift.inputs[0])
for frame, offset in [(1, 0), (48, -2.6)]:
    shift.inputs[1].default_value = (offset, 0, 0)
    shift.inputs[1].keyframe_insert('default_value', frame=frame)
for curve in teal.node_tree.animation_data.action.layers[0].strips[0].channelbag(
        teal.node_tree.animation_data.action_slot).fcurves:
    for key in curve.keyframe_points:
        key.interpolation = 'LINEAR'
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.5
noise.inputs['Detail'].default_value = 2
links.new(shift.outputs[0], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .18
ramp.color_ramp.elements[0].color = (.024, .22, .25, 1)
ramp.color_ramp.elements[1].position = .84
ramp.color_ramp.elements[1].color = (.083, .39, .41, 1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
shader = nodes.get('Principled BSDF')
links.new(ramp.outputs[0], shader.inputs['Base Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .14
bump.inputs['Distance'].default_value = .027
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs[0], shader.inputs['Normal'])

for side in (-1, 1):
    def terrain(x, distances):
        rail = [(edge(x, side) + side*d, h) for d, h in distances]
        return rail if side == 1 else rail[::-1]

    strip('Wet shore', lambda x: terrain(x, [(-.12, -.10), (.08, .055),
                                              (.27, .15)]), wet)
    strip('Gravel shore', lambda x: terrain(x, [(.27, .15), (.41, .23),
                                                 (.75+.05*sin(x*2), .38)]), sand)
    strip('Meadow', lambda x: terrain(x, [(.75+.05*sin(x*2), .38),
                                         (1.4, .40), (3.4, .48), (19, .62)]),
          grass if side == -1 else far_grass)

    for i in range(44):
        x = rng.uniform(-14, 14)
        d = rng.uniform(.14, .75)
        size = rng.uniform(.035, .14)
        sphere('Shore pebble', (x, edge(x, side)+side*d, .057+.44*d),
               (size*1.48, size, size*.65), rng.choice(stone), True
               ).rotation_euler.z = rng.uniform(0, 6.28)

    for i in range(41):
        x = rng.uniform(-13, 13)
        y = edge(x, side) + side*rng.uniform(.80, 2.6)
        if side == -1 and abs(x+2.8) < .72:
            continue
        vertices, faces = [], []
        for j in range(rng.randint(4, 8)):
            a, b = x+rng.uniform(-.12, .12), y+rng.uniform(-.10, .10)
            h = rng.uniform(.11, .33)
            bend = rng.uniform(-.15, .15)
            k = len(vertices)
            vertices.extend([(a-.023,b,.38), (a+.023,b,.38),
                             (a+bend*.45,b+.033,.39+h*.62),
                             (a+bend,b+.07,.39+h)])
            faces.extend([(k,k+1,k+2), (k,k+2,k+3)])
        mesh('Tuft of rushes', vertices, faces, rng.choice(blades))

# Thin surface ribbons trace the channel. The midstream ribbons travel fastest.
def ribbon(name, length, width, bend, mat):
    vertices = []
    for j in range(13):
        t = j/12
        w = width * max(.025, sin(math.pi*t)**.72)
        y = bend*sin(math.pi*t) + width*.19*sin(8*t)
        vertices.extend([(t*length, y-w, 0), (t*length, y+w, 0)])
    return mesh(name, vertices,
                [(2*j, 2*j+2, 2*j+3, 2*j+1) for j in range(12)], mat)


for i in range(152):
    x = rng.uniform(-17, 12)
    lane = rng.uniform(-.92, .92)
    length = rng.uniform(.24, 1.58)
    obj = ribbon('Drifting surface streak', length, rng.uniform(.009, .047),
                 rng.uniform(-.046, .046), rng.choices(foam, [43, 39, 15, 3])[0])
    speed = 1.87 - .87*abs(lane)**2
    for frame in range(1, 49):
        along = x + (frame-1)*speed/12
        axis = center(along)
        obj.location = (along, axis + lane*(edge(along, 1 if lane >= 0 else -1)
                                             - axis)* (1 if lane >= 0 else -1), .012)
        obj.rotation_euler.z = math.atan2(center(along+.04)-axis, .04)
        obj.keyframe_insert('location', frame=frame)
        obj.keyframe_insert('rotation_euler', frame=frame)

# A split wake marks downstream even in a still frame.
for x, lane, size in [(.8, .98, .47), (3.8, -1.30, .30), (-5.9, -.95, .32)]:
    y = center(x)+lane
    sphere('Partly submerged boulder', (x, y, .005), (size, size*.71, size*.67),
           stone[0], True).rotation_euler.z = -.24
    for sign in (-1, 1):
        for j in range(3):
            obj = ribbon('Boulder wake', size*(2.55-j*.42), .018-j*.003,
                         sign*size*.12, foam[2 if j == 0 else 1])
            obj.location = (x-size*.49+j*.13, y+sign*size*(.65+j*.22), .021)
            obj.rotation_euler.z = sign*(.11+j*.07)

# Hiker built in local coordinates with +Y facing the river.
coat = material('Saffron rain jacket', (.70, .27, .047))
coat_dark = material('Jacket cuffs and hood', (.52, .16, .031))
pants = material('Slate trousers', (.055, .087, .10))
boots = material('Dark leather boots', (.089, .061, .042))
skin = material('Warm clay skin', (.55, .28, .15))
hair = material('Dark hair', (.09, .053, .032))
cap = material('Oxblood cap', (.30, .062, .041))
pack = material('Canvas daypack', (.105, .18, .15))
strap = material('Pack trim', (.21, .26, .17))
eye = material('Eyes', (.043, .031, .027))


def pivot(name, parent=None, point=(0,0,0)):
    obj = bpy.data.objects.new(name, None)
    scene.collection.objects.link(obj)
    obj.parent = parent
    obj.location = point
    return obj


hiker = pivot('Watcher', point=(-2.75, edge(-2.75, -1)-.98, .385))
hiker.rotation_euler.z = -.79
upper = pivot('Breathing and weight shift', hiker, (0,0,.95))
head = pivot('Gaze follows the current', upper, (0,.035,.64))


def part(parent, name, point, scale, mat):
    obj = sphere(name, point, scale, mat)
    obj.parent = parent
    return obj


def joint(parent, name, a, b, width, depth, mat):
    obj = limb(name, a, b, width, depth, mat)
    obj.parent = parent
    return obj


for sign, forward in [(-1, -.105), (1, .115)]:
    hip = (sign*.136, -.035, .99)
    knee = (sign*.17, forward*.55+.02, .54)
    ankle = (sign*.19, forward, .145)
    joint(hiker, 'Trouser thigh', hip, knee, .132, .130, pants)
    joint(hiker, 'Trouser calf', knee, ankle, .101, .100, pants)
    part(hiker, 'Boot', (ankle[0], forward+.064, .103), (.115,.204,.105), boots)
    part(hiker, 'Boot sole', (ankle[0], forward+.067, .043), (.12,.207,.044), pants)

part(upper, 'Jacket hem', (0,-.022,.008), (.287,.182,.150), coat_dark)
part(upper, 'Rain jacket', (0,0,.275), (.325,.205,.366), coat)
part(upper, 'Folded hood', (0,-.156,.528), (.236,.145,.119), coat_dark)
part(upper, 'Neck', (0,.022,.615), (.105,.102,.123), skin)
part(upper, 'Daypack', (0,-.241,.269), (.24,.166,.287), pack)
part(upper, 'Daypack front pocket', (0,-.373,.192), (.197,.063,.135), strap)
for sign in (-1, 1):
    joint(upper, 'Shoulder strap', (sign*.208,.138,.143), (sign*.206,.130,.508),
          .044,.045,pack)
    joint(upper, 'Strap over shoulder', (sign*.206,.13,.50),
          (sign*.19,-.19,.53), .043,.047,pack)
    shoulder = (sign*.279,.012,.456)
    elbow = (sign*.352,.065,.215)
    hand = (sign*.321,.152,.043)
    joint(upper, 'Upper sleeve', shoulder, elbow, .109,.113,coat)
    joint(upper, 'Forearm sleeve', elbow, hand, .087,.090,coat)
    part(upper, 'Cuff', (hand[0],hand[1],hand[2]-.013), (.075,.078,.065),coat_dark)
    part(upper, 'Hand', (hand[0],hand[1]+.016,hand[2]-.063), (.064,.057,.095),skin)

part(head, 'Hair', (0,-.044,.152), (.178,.157,.186), hair)
part(head, 'Face', (0,.037,.135), (.161,.148,.188), skin)
part(head, 'Nose', (0,.173,.128), (.043,.049,.043), skin)
for sign in (-1, 1):
    part(head, 'Ear', (sign*.154,.011,.116), (.038,.044,.060), skin)
    part(head, 'Eye', (sign*.073,.161,.163), (.023,.013,.018), eye)
part(head, 'Cap crown', (0,-.013,.273), (.187,.18,.088),cap)
part(head, 'Cap brim', (0,.12,.239), (.181,.185,.022),cap)

for frame, yaw, pitch, lean, rise in [(1,.31,-.22,.038,0), (11,.30,-.20,.037,.009),
                                      (25,.04,-.255,.060,.003), (39,-.24,-.24,.052,.011),
                                      (48,-.28,-.238,.048,.004)]:
    head.rotation_euler = (pitch, 0, yaw)
    upper.rotation_euler = (-lean, .014*cos(frame*.12), -.11*(1-yaw))
    upper.location.z = .95+rise
    head.keyframe_insert('rotation_euler', frame=frame)
    upper.keyframe_insert('rotation_euler', frame=frame)
    upper.keyframe_insert('location', frame=frame)


def aim(obj, point):
    obj.rotation_euler = (Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()


bpy.ops.object.camera_add(location=(5.7,-11.7,9.1))
camera = bpy.context.object
aim(camera, (-.15,-.24,.23))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 12.5
scene.camera = camera

world = bpy.data.worlds.new('Soft blue daylight')
world.use_nodes = True
world.node_tree.nodes.get('Background').inputs[0].default_value = (.55,.68,.77,1)
world.node_tree.nodes.get('Background').inputs[1].default_value = .37
scene.world = world
bpy.ops.object.light_add(type='SUN', location=(-5,-4,9))
sun = bpy.context.object
aim(sun, (0,0,0))
sun.data.energy = 2.1
sun.data.angle = .16
sun.data.color = (1,.86,.69)
bpy.ops.object.light_add(type='AREA', location=(2,6,7))
fill = bpy.context.object
aim(fill, (0,0,0))
fill.data.energy = 340
fill.data.shape = 'DISK'
fill.data.size = 8

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start = 1
scene.frame_end = 48
scene.view_settings.view_transform = 'AgX'
scene.frame_set(1)
