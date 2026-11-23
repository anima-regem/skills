"""River watch. Build with Blender --background --factory-startup --python scene.py."""
from pathlib import Path
from math import atan2, cos, exp, hypot, sin, pi, radians
import random

import bpy
from mathutils import Vector, Quaternion

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, 48
scene.render.fps = 12
scene.render.fps_base = 1
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
rng = random.Random(71)


def paint(name, rgb, roughness=.75, glow=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Emission Color'].default_value = (*rgb, 1)
    p.inputs['Emission Strength'].default_value = glow
    return mat


def mesh(name, verts, faces, material):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob


def linear_keys(ob):
    action = ob.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for fcurve in strip.channelbag(ob.animation_data.action_slot).fcurves:
                for key in fcurve.keyframe_points:
                    key.interpolation = 'LINEAR'


# The gentle S curve has a broad, smooth mid-channel and shallow gravel margins.
# Speeds and ripple sizes are art-directed estimates at human scale.
def near(x):
    return -1.33 + .23*sin(.52*x) + .27*sin(.24*x + .6)


def far(x):
    return 2.39 + .31*sin(.49*x + .75) + .26*sin(.21*x)


def lane(x, u):
    return near(x) + u*(far(x)-near(x))


def surface(name, rows, material):
    verts = [(x, y(x), z(x)) for x in (-24 + i*.25 for i in range(193)) for y, z in rows]
    n = len(rows)
    faces = [(i*n+j, (i+1)*n+j, (i+1)*n+j+1, i*n+j+1)
             for i in range(192) for j in range(n-1)]
    return mesh(name, verts, faces, material)


grass = paint('Dry sage grass', (.205, .247, .087))
grass_far = paint('Far meadow', (.139, .207, .097))
earth = paint('Warm clay bank', (.32, .192, .099))
wet = paint('Wet gravel', (.198, .166, .098))
edge = paint('Clear shallows', (.061, .29, .273), .37, .10)
water = paint('Blue-green current', (.024, .225, .254), .30, .15)

# A quiet mottling on the large meadow surfaces keeps the banks from reading as flat color cards.
for material in (grass, grass_far, earth):
    tree = material.node_tree
    texture = tree.nodes.new('ShaderNodeTexNoise')
    texture.inputs['Scale'].default_value = 5.5
    texture.inputs['Detail'].default_value = 2.5
    uv = tree.nodes.new('ShaderNodeTexCoord')
    tree.links.new(uv.outputs['Object'], texture.inputs['Vector'])
    colors = tree.nodes.new('ShaderNodeValToRGB')
    for el, value, factor in zip(colors.color_ramp.elements, (.19,.8), (.73,1.19)):
        el.position = value
        el.color = (*(c*factor for c in material.diffuse_color[:3]),1)
    tree.links.new(texture.outputs['Fac'], colors.inputs[0])
    tree.links.new(colors.outputs[0], tree.nodes.get('Principled BSDF').inputs['Base Color'])

for shore, sign, turf in [(near, -1, grass), (far, 1, grass_far)]:
    def row(offset, height):
        return (lambda x: shore(x)+sign*offset, lambda x: height)
    for title, a, b, mat in [
        ('Submerged shelf', (-.26, -.10), (0, .015), wet),
        ('Cut bank', (0, .015), (.40, .42), earth),
        ('Bank lip', (.40,.42), (.80,.42), turf),
        ('Meadow', (.80,.42), (24,.42), turf),
    ]:
        rows = [row(*a), row(*b)]
        surface(title, rows if sign > 0 else rows[::-1], mat)
surface('River', [(lambda x, u=u: lane(x,u), lambda x: 0)
                  for u in [-.10, .03, .13, .28, .50, .72, .87, .97, 1.1]], water)
surface('Near shoal', [(lambda x, u=u: lane(x,u), lambda x: .003)
                       for u in [-.01, .035]], edge)
surface('Far shoal', [(lambda x, u=u: lane(x,u), lambda x: .003)
                      for u in [.949, 1.01]], edge)

# Advect a stretched material pattern together with the surface glints.
nodes = water.node_tree.nodes
links = water.node_tree.links
coords = nodes.new('ShaderNodeTexCoord')
shift = nodes.new('ShaderNodeVectorMath')
shift.operation = 'ADD'
links.new(coords.outputs['Object'], shift.inputs[0])
for frame, x in [(1, 0), (48, -3.7)]:
    shift.inputs[1].default_value[0] = x
    shift.inputs[1].keyframe_insert(data_path='default_value', index=0, frame=frame)
linear_keys(water.node_tree)
stretch = nodes.new('ShaderNodeVectorMath')
stretch.operation = 'MULTIPLY'
stretch.inputs[1].default_value = (.66, 4.4, 1)
links.new(shift.outputs[0], stretch.inputs[0])
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 2.0
noise.inputs['Detail'].default_value = 2.2
links.new(stretch.outputs[0], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .18
ramp.color_ramp.elements[0].color = (.017, .145, .174, 1)
ramp.color_ramp.elements[1].position = .82
ramp.color_ramp.elements[1].color = (.072, .327, .344, 1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
links.new(ramp.outputs[0], nodes.get('Principled BSDF').inputs['Base Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .21
bump.inputs['Distance'].default_value = .033
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs[0], nodes.get('Principled BSDF').inputs['Normal'])

glints = [paint('Current glint', color, .50, .34)
          for color in [(.17,.41,.405), (.3,.58,.536), (.48,.72,.64)]]
leaf_mat = paint('Amber floating leaves', (.96,.44,.049), .50, .22)
leaf_vein = paint('Leaf fold', (.54,.18,.026), .61, .1)


def ribbon(name, length, width, curve, mat):
    verts = []
    for i in range(9):
        t = i/8
        y = curve*sin(pi*t)
        w = .5*width*(.012 + sin(pi*t)**.72)
        verts.extend([(length*t, y-w, 0), (length*t, y+w, 0)])
    return mesh(name, verts, [(2*i,2*i+2,2*i+3,2*i+1) for i in range(8)], mat)


def velocity(u):
    # Bank drag slows the margins. https://pubs.usgs.gov/wri/1981/0071/report.pdf
    return .43 + .64*sin(pi*u)**.8


def drift(ob, x, u, speed, height, tilt=0, length=0):
    for f in (1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 48):
        t = (f-1)/12
        travel = x+t*speed
        # Split the surface flow around the exposed rock, with an anchored wake.
        cross = u-.70
        bypass = (.084 if cross >= 0 else -.084)*exp(-(cross/.082)**2)
        bypass *= exp(-((travel+.5*length-2.73)/.97)**2)
        ob.location = (travel, lane(travel,u+bypass), height+.002*sin(5*t+x))
        ob.rotation_euler.z = tilt + .055*cos(.52*travel)
        ob.keyframe_insert(data_path='location', frame=f)
        ob.keyframe_insert(data_path='rotation_euler', frame=f)
    linear_keys(ob)


for i in range(119):
    u = rng.uniform(.052,.95)
    length = rng.uniform(.18,.86)
    ob = ribbon('Drifting surface glint', length,
                rng.uniform(.014,.045), rng.uniform(-.023,.023),
                rng.choices(glints, [6,4,1])[0])
    drift(ob, rng.uniform(-13,10), u, velocity(u)*rng.uniform(.87,1.12), .012, length=length)


def leaf(x, u, size, angle):
    ob = mesh('Floating alder leaf', [(-.54,0,0),(-.21,-.29,.012),
              (.23,-.25,.017),(.56,0,0),(.22,.24,.016),(-.24,.22,.008),
              (0,0,.12)], [(i,(i+1)%6,6) for i in range(6)], leaf_mat)
    ob.data.materials.append(leaf_vein)
    for i in (0,5):
        ob.data.polygons[i].material_index = 1
    ob.scale = (size, size, size)
    drift(ob,x,u,velocity(u),.017,angle)
    return ob


tracked_leaf = leaf(-3.75,.35,.23,-.31)
tracked_leaf.name = 'Leaf followed by the watcher'
for x,u,size,angle in [(-6.5,.52,.14,.6),(-.9,.69,.13,-.52),(2.1,.31,.16,.14),
                       (4.0,.78,.12,.7),(-5.8,.26,.12,-.5),(.4,.42,.10,.7)]:
    leaf(x,u,size,angle)

rock_mats = [paint('River stone', c) for c in
             [(.25,.29,.234), (.36,.363,.28), (.19,.234,.209)]]


def stone(location, scale, index):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=location)
    ob = bpy.context.object
    ob.name = 'Rounded river stone'
    ob.scale = scale
    ob.rotation_euler = (rng.uniform(-.2,.2),rng.uniform(-.14,.14),rng.random()*pi)
    ob.data.materials.append(rock_mats[index])
    return ob


for shore, sign in [(near,-1),(far,1)]:
    for i in range(48):
        x = rng.uniform(-11,11)
        offset = rng.uniform(-.07,.42)
        radius = rng.uniform(.042,.155)
        z = .02 + max(0,offset)*.97
        stone((x,shore(x)+sign*offset,z), (radius,radius*.73,radius*.46),i%3)

stone((2.73, lane(2.73,.70), .018), (.32,.23,.19), 2)
for side in (-1, 1):
    ob = ribbon('Standing wake', 1.35, .038, side*.125, glints[1])
    ob.location = (2.65,lane(2.73,.70)+side*.19,.019)
    ob.rotation_euler.z = side*.13


# Sparse clumps give the bank a silhouette and a recognizable scale.
for sign, shore in [(-1,near),(1,far)]:
    for idx, rgb in enumerate([(.28,.32,.105), (.37,.385,.138), (.163,.239,.095)]):
        blades = paint('Sedge blade',rgb)
        verts, faces = [], []
        for _ in range(41):
            x = rng.uniform(-11,11)
            y = shore(x)+sign*rng.uniform(.44,1.75)
            if sign < 0 and abs(x+2.65) < .57:
                continue
            h = rng.uniform(.13,.39)
            for _ in range(rng.randint(4,8)):
                dx,dy = rng.uniform(-.10,.10),rng.uniform(-.075,.075)
                b = Vector((x+dx,y+dy,.419))
                width = rng.uniform(.013,.028)
                across = Vector((cos(idx+57*dx),sin(idx+57*dx),0))*width
                slope = Vector((dx*1.25+.04,dy*1.5,h*rng.uniform(.55,1.2)))
                k = len(verts)
                verts.extend([b-across,b+across,b+slope*.56+across*.55,
                              b+slope,b+slope*.56-across*.55])
                faces.extend([(k,k+1,k+2,k+4),(k+4,k+2,k+3)])
        mesh('Bank sedges',verts,faces,blades)

for x,y,s in [(-4.9,-2.63,.37), (-5.3,-2.77,.24), (4.3,-2.4,.34),
              (-3.85,3.05,.31), (-3.42,3.19,.23), (3.9,3.37,.38)]:
    stone((x,y,.42),(s,s*.66,s*.43),rng.randrange(3))

# KinemIQ Mannequin and Idle_relaxed, CC0 v1.0, supplied as watcher.glb.
# https://github.com/Kinemiq/free-game-animations/releases/tag/v1.0
bpy.ops.import_scene.gltf(filepath=str(Path(__file__).resolve().parent / 'assets' / 'watcher.glb'))
rig = next(o for o in bpy.context.selected_objects if o.type == 'ARMATURE')
body = bpy.data.objects['SuperHero_Male']
bones = rig.pose.bones
head = bones['Head']
poses = []
for frame in range(1,49):
    source_frame = 1 + (frame-1)*.57
    scene.frame_set(int(source_frame), subframe=source_frame%1)
    poses.append({b.name: b.matrix_basis.copy() for b in bones})

rig.animation_data_clear()
for b in bones:
    b.matrix_basis = poses[0][b.name]
bpy.context.view_layer.update()

jacket = paint('Ochre field jacket', (.65,.235,.045))
pants = paint('Slate trousers', (.053,.102,.126))
boot = paint('Dark leather boots', (.046,.038,.027))
skin = paint('Warm skin', (.49,.257,.136))
hair = paint('Dark hair', (.069,.034,.020))
cuff = paint('Jacket cuffs and hem', (.37,.103,.025))
body.data.materials.clear()
for mat in (jacket,pants,boot,skin,hair,cuff):
    body.data.materials.append(mat)

group_names = {g.index:g.name.lower() for g in body.vertex_groups}
def dominant(vertex):
    return group_names[max(vertex.groups, key=lambda g:g.weight).group] if vertex.groups else ''

for face in body.data.polygons:
    vs = [body.data.vertices[i] for i in face.vertices]
    z = sum(v.co.z for v in vs)/len(vs)
    y = sum(v.co.y for v in vs)/len(vs)
    names = [dominant(v) for v in vs]
    name = max(names, key=names.count)
    if name.startswith(('head','neck')):
        face.material_index = 4 if z > 1.69 + max(0,-y-.13)*.42 else 3
    elif name.startswith(('hand','thumb','index','middle','ring','pinky')):
        face.material_index = 3
    elif name.startswith(('foot','ball')) or z < .14:
        face.material_index = 2
    elif name.startswith(('thigh','calf')) or z < .86:
        face.material_index = 1
    elif .86 <= z < .93:
        face.material_index = 5

for name, mat in [('Eyebrows',hair),('Eyes',boot)]:
    ob = bpy.data.objects[name]
    ob.data.materials.clear()
    ob.data.materials.append(mat)

# Place the fixed shoe soles just into the turf, using the evaluated skin.
evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
sole = min((evaluated.matrix_world @ v.co).z for v in evaluated.data.vertices)
rig.location = (-2.65, -2.42, .418-sole)
rig.rotation_quaternion = Quaternion((0,0,1),radians(161))

# Keep the source stance below the waist. The upper-body idle provides
# breathing and the neck/head action follows the leaf from left to right.
upper = [b for b in bones if b.name.startswith(('spine','neck','Head','clavicle',
           'upperarm','lowerarm','hand'))]
# Express the face directions in the head's bind space for a stable aim.
bind_head = head.bone.matrix_local.to_quaternion()

for f, pose in enumerate(poses, 1):
    scene.frame_set(f)
    for b in upper:
        # Keep upper-body translation at the planted pose.
        b.rotation_mode = 'QUATERNION'
        initial = poses[0][b.name].to_quaternion()
        b.rotation_quaternion = initial.slerp(pose[b.name].to_quaternion(),.58)
    bpy.context.view_layer.update()
    target = tracked_leaf.location.copy()
    target.x += .24
    target.z += .22
    target = rig.matrix_world.inverted() @ target
    delta = target-head.head
    yaw = atan2(delta.x, -delta.y)*.88
    pitch = atan2(-delta.z,hypot(delta.x,delta.y))*.91
    facing = Quaternion((0,0,1),yaw) @ Quaternion((1,0,0),pitch)
    m = (facing @ bind_head).to_matrix().to_4x4()
    m.translation = head.head
    head.matrix = m
    for b in upper:
        b.keyframe_insert(data_path='rotation_quaternion',frame=f,group=b.name)
linear_keys(rig)


def aim(ob, target):
    ob.rotation_euler = (Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()


bpy.ops.object.camera_add(location=(.85,-10.6,7.15))
camera = bpy.context.object
camera.name = 'River overlook'
aim(camera,(.30,.05,.22))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 10.6
scene.camera = camera

background = scene.world.node_tree.nodes.get('Background')
background.inputs['Color'].default_value = (.55,.68,.81,1)
background.inputs['Strength'].default_value = .37

bpy.ops.object.light_add(type='SUN', location=(-4,1.5,7))
sun = bpy.context.object
sun.name = 'Late afternoon sun'
aim(sun,(0,0,0))
sun.data.energy = 2.25
sun.data.angle = radians(10)
sun.data.color = (1,.88,.71)

bpy.ops.object.light_add(type='AREA', location=(1,-3,6))
fill = bpy.context.object
fill.name = 'Open sky fill'
fill.data.energy = 390
fill.data.shape = 'DISK'
fill.data.size = 8
fill.data.color = (.66,.81,1)
aim(fill,(0,0,0))

scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
