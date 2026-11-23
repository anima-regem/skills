"""Build a four-second river study in Blender 5.2."""
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

random.seed(14)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'


def paint(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = mat.diffuse_color
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


def stone(name, position, scale, mat, detail=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=detail, radius=1, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler.z = random.uniform(0, math.tau)
    obj.data.materials.append(mat)
    return obj


def linear(obj, path, start, end):
    for frame, value in [(1, start), (48, end)]:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)
    for curve in obj.animation_data.action.layers[0].strips[0].channelbag(
        obj.animation_data.action_slot
    ).fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'


def shore(x, side):
    return (-2.38 if side < 0 else 3.0) + 0.29 * math.sin(x * 0.47 + 0.5) + (
        0.12 * math.sin(x * 1.1 + side)
    )


meadow = paint('Lichen green', (0.24, 0.32, 0.132))
silt = paint('Warm exposed silt', (0.43, 0.295, 0.144))
wet = paint('Wet shoreline', (0.23, 0.183, 0.095))
for ground in (meadow, silt):
    nodes = ground.node_tree.nodes
    links = ground.node_tree.links
    grain = nodes.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = 2.6
    links.new(nodes.new('ShaderNodeTexCoord').outputs['Object'], grain.inputs['Vector'])
    tint = nodes.new('ShaderNodeValToRGB')
    for stop, factor in zip(tint.color_ramp.elements, (.73, 1.16)):
        stop.color = (*(c*factor for c in ground.diffuse_color[:3]), 1)
    links.new(grain.outputs['Fac'], tint.inputs['Fac'])
    links.new(tint.outputs['Color'], nodes.get('Principled BSDF').inputs['Base Color'])
for side in (-1, 1):
    profile = [(-0.18, -0.11), (0.0, 0.015), (0.16, 0.105),
               (0.43, 0.29), (0.76, 0.38), (2.1, 0.38), (18, 0.41)]
    verts, faces = [], []
    for i in range(121):
        x = (i - 60) * 0.32
        for width, height in profile:
            verts.append((x, shore(x, side) + side * width, height))
    n = len(profile)
    for i in range(120):
        for j in range(n - 1):
            a = i * n + j
            face = (a, a + n, a + n + 1, a + 1)
            faces.append(face if side > 0 else face[::-1])
    bank = mesh('Graded riverbank', verts, faces, meadow)
    bank.data.materials.append(silt)
    bank.data.materials.append(wet)
    for poly in bank.data.polygons:
        poly.material_index = (2, 2, 1, 1, 0, 0)[poly.index % (n - 1)]

# The opaque, illustrated surface has a static depth gradient and advected texture.
water = paint('Jade water', (0.04, 0.26, 0.28), 0.33)
tree = water.node_tree
tex = tree.nodes.new('ShaderNodeTexCoord')
depth = tree.nodes.new('ShaderNodeVertexColor')
depth.layer_name = 'Channel depth'
current = bpy.data.objects.new('Water texture advection', None)
scene.collection.objects.link(current)
linear(current, 'location', (0, 0, 0), (4.8, 0, 0))
tex.object = current
stretch = tree.nodes.new('ShaderNodeVectorMath')
stretch.operation = 'MULTIPLY'
stretch.inputs[1].default_value = (0.53, 3.6, 1)
tree.links.new(tex.outputs['Object'], stretch.inputs[0])
noise = tree.nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 2.25
noise.inputs['Detail'].default_value = 2
tree.links.new(stretch.outputs[0], noise.inputs['Vector'])
mix = tree.nodes.new('ShaderNodeMixRGB')
mix.blend_type = 'SOFT_LIGHT'
mix.inputs[0].default_value = 0.40
tree.links.new(depth.outputs['Color'], mix.inputs[1])
tree.links.new(noise.outputs['Fac'], mix.inputs[2])
shader = tree.nodes.get('Principled BSDF')
tree.links.new(mix.outputs[0], shader.inputs['Base Color'])
bump = tree.nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = 0.16
bump.inputs['Distance'].default_value = 0.032
tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
tree.links.new(bump.outputs[0], shader.inputs['Normal'])
verts, faces = [], []
for i in range(121):
    x = (i - 60) * 0.32
    for j in range(17):
        u = j / 16
        verts.append((x, (shore(x, -1) - .09) * (1-u) + (shore(x, 1) + .09) * u, 0))
    if i:
        for j in range(16):
            a = (i-1)*17+j
            faces.append((a, a+17, a+18, a+1))
surface = mesh('River surface', verts, faces, water)
colors = surface.data.color_attributes.new(name='Channel depth', type='FLOAT_COLOR', domain='POINT')
for i, entry in enumerate(colors.data):
    t = math.sin(math.pi * (i % 17) / 16) ** 0.64
    entry.color = (0.105 - 0.075*t, 0.40 - 0.176*t, 0.315 - 0.066*t, 1)

shale = [paint('Pebble • ' + str(i), c) for i, c in enumerate(
    [(0.25, .28, .24), (.35, .38, .32), (.43, .39, .29)])]
for side in (-1, 1):
    for center in (-5.6, -0.8, 3.5, 6.9):
        for i in range(12):
            x = center + random.uniform(-0.8, 0.8)
            d = random.uniform(0.12, .63)
            r = random.uniform(.04, .17)
            stone('Shore pebble', (x, shore(x, side)+side*d, .05+.42*d),
                  (r*1.4, r, r*.65), random.choice(shale), 1 if i % 4 else 2)

reed_mats = [paint('Sedge • ' + str(i), c) for i, c in enumerate(
    [(.16,.23,.078), (.31,.39,.119), (.49,.44,.16)])]
verts, faces, blades = [], [], []
for side, groups in [(-1, [-6.0, -5.45, -4.95, 0.0, 2.95, 3.48, 5.95]),
                     (1, [-7.5, -5.6, -4.4, -2.0, -.9, 1.9, 2.55, 4.8, 7.1])]:
    for center in groups:
        for _ in range(22):
            x = center + random.uniform(-.36, .36)
            y = shore(x, side) + side * random.uniform(.55, 1.12)
            h = random.uniform(.12, .56)
            w = random.uniform(.016, .043)
            a = random.random() * math.tau
            dx, dy = math.cos(a), math.sin(a)
            bend = random.uniform(.12, .48) * h
            i = len(verts)
            for f in (0, .55, .83):
                for k in (-1, 1):
                    verts.append((x + dx*k*w*(1-f)/2 - dy*bend*f*f,
                                  y + dy*k*w*(1-f)/2 + dx*bend*f*f, .34+h*f))
            verts.append((x-dy*bend, y+dx*bend, .34+h))
            faces.extend([(i,i+1,i+3,i+2),(i+2,i+3,i+5,i+4),(i+4,i+5,i+6)])
            blades.extend([random.randrange(3)]*3)
sedges = mesh('River sedges', verts, faces, reed_mats[0])
for mat in reed_mats[1:]:
    sedges.data.materials.append(mat)
for poly, index in zip(sedges.data.polygons, blades):
    poly.material_index = index

bright = paint('Pale water glints', (.31,.65,.57), .42)
quiet = paint('Subtle water glints', (.14,.425,.395), .42)


def ripple(x, y, length, width, wave):
    v = []
    for i in range(9):
        u = i/8
        center = y + wave * math.sin(u * math.pi)
        half = width * math.sin(math.pi*u)**0.7 / 2
        v.extend([(x+length*u, center-half, .013), (x+length*u, center+half, .013)])
    return v


for lane in range(15):
    y = -1.97 + lane*.304
    speed = (0.66 + 0.76 * math.sin(math.pi * (lane+1)/16)) * 47/12
    for accent, mat in enumerate((quiet, bright)):
        verts, faces = [], []
        for j in range(12 if not accent else 4):
            x = -15 + j * (2.65 if not accent else 7.3) + random.uniform(-1.4, 1.4)
            i = len(verts)
            verts.extend(ripple(x, y+random.uniform(-.13,.13), random.uniform(.21,.94),
                                random.uniform(.014,.041), random.uniform(-.036,.036)))
            faces.extend((i+k,i+k+2,i+k+3,i+k+1) for k in range(0,16,2))
        glints = mesh('Drifting surface streaks', verts, faces, mat)
        linear(glints, 'location', (0,0,0), (speed,0,0))

# The fixed bow ripple splits around the exposed stone and trails downstream.
stone('Water-worn boulder', (2.8,1.39,.035), (.42,.30,.24), shale[0])
for sign in (-1, 1):
    verts, faces = [], []
    for i in range(21):
        t = i/20
        x = 2.42 + 1.49*t
        y = 1.39 + sign*(.08 + .32*math.sin(math.pi*t)**.72)
        width = .041*math.sin(math.pi*t)**.8
        verts.extend([(x,y-width/2,.016),(x,y+width/2,.016)])
        if i:
            k = i*2
            faces.append((k-2,k,k+1,k-1))
    mesh('Boulder wake', verts, faces, bright)

leaf_mat = paint('Golden floating leaves', (.85,.355,.048))
vein = paint('Leaf midrib', (.4,.15,.027))
for j, (x, y, size) in enumerate([(-3.0,-1.00,.29), (-3.42,-.87,.15), (-3.75,-1.11,.11)]):
    leaf = mesh('Drifting alder leaf',
                [(-.55,0,0),(-.2,-.29,0),(.27,-.22,.012),(.55,0,.027),
                 (.22,.25,.016),(-.23,.26,0),(.0,0,.096)],
                [(6,i,(i+1)%6) for i in range(6)], leaf_mat)
    if j == 0:
        lead_leaf = leaf
    leaf.scale = (size, size, size)
    ridge = mesh('Leaf midrib', [(-.48,0,.015),(0,-.024,.101),(.46,0,.046),(0,.024,.101)],
                 [(0,1,3),(1,2,3)], vein)
    ridge.parent = leaf
    travel = 4.85 + j*.065
    for frame in range(1, 49):
        t = (frame-1)/47
        leaf.location = (x+travel*t, y+.035*math.sin(t*7+j), .021+.007*math.sin(t*21+j))
        leaf.rotation_euler = (.14*math.sin(t*14+j), .12*math.sin(t*11+j), .25+j+0.48*t)
        leaf.keyframe_insert(data_path='location', frame=frame)
        leaf.keyframe_insert(data_path='rotation_euler', frame=frame)
    if j == 0:
        for sign in (-1, 1):
            wake_verts = ripple(-.43, sign*.069, .33, .017, -sign*.025)
            wake = mesh('Leaf wake', wake_verts, [(k,k+2,k+3,k+1) for k in range(0,16,2)], quiet)
            linear(wake, 'location', (x,y,0), (x+travel,y,0))

# The supplied KinemIQ idle is sampled at half speed. Legs and pelvis hold
# the supported starting pose while the upper body breathes and follows the leaf.
bpy.ops.import_scene.gltf(filepath=str(Path(__file__).resolve().parent / 'assets' / 'watcher.glb'))
rig = next(o for o in bpy.context.selected_objects if o.type == 'ARMATURE')
body = bpy.data.objects['SuperHero_Male']
idle = bpy.data.actions['Idle_relaxed']
anim = rig.animation_data
for track in list(anim.nla_tracks):
    anim.nla_tracks.remove(track)
anim.action = idle
anim.action_slot = idle.slots[0]
poses = []
for frame in range(1, 49):
    source = (frame-1)*.5
    scene.frame_set(int(source), subframe=source%1)
    poses.append({bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones})
rig.animation_data_clear()
rig.location = (-2.55, -3.47, .38)
rig.rotation_mode = 'XYZ'
rig.rotation_euler.z = math.radians(140)
skin = paint('Warm terracotta skin', (.47,.235,.119))
coat = paint('Burnt orange field jacket', (.57,.117,.035))
pants = paint('Deep blue trousers', (.029,.077,.101))
boots = paint('Leather boots', (.051,.036,.027))
hat = paint('Ochre knit cap', (.59,.315,.075))
body.data.materials.clear()
for mat in (skin, coat, pants, boots):
    body.data.materials.append(mat)
for poly in body.data.polygons:
    x, y, z = sum((body.data.vertices[i].co for i in poly.vertices), Vector()) / len(poly.vertices)
    poly.material_index = 3 if z < .117 else 2 if z < .965 else 1 if z < 1.526 and abs(x)<.693 else 0
bpy.data.objects['Eyebrows'].data.materials[0] = boots
bpy.data.objects['Eyes'].data.materials[0] = boots

head = rig.pose.bones['Head']
rest_forward = head.bone.matrix_local.to_quaternion().inverted() @ Vector((0,-1,0))
for frame, pose in enumerate(poses, 1):
    scene.frame_set(frame)
    for bone in rig.pose.bones:
        basis = pose if bone.name.startswith(('spine', 'neck', 'Head', 'head', 'clavicle',
                                              'upperarm', 'lowerarm', 'hand')) else poses[0]
        bone.matrix_basis = basis[bone.name]
    bpy.context.view_layer.update()
    arm_rotation = head.matrix.to_quaternion()
    forward = arm_rotation @ rest_forward
    leaf_in_rig = rig.matrix_world.inverted() @ lead_leaf.location
    correction = forward.rotation_difference(leaf_in_rig - head.head)
    head.rotation_quaternion = (head.rotation_quaternion @ arm_rotation.inverted()
                                @ correction @ arm_rotation)
    for bone in rig.pose.bones:
        bone.keyframe_insert(data_path='location', frame=frame)
        bone.keyframe_insert(data_path='rotation_quaternion', frame=frame)
        bone.keyframe_insert(data_path='scale', frame=frame)

scene.frame_set(1)
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
bottom = min((evaluated.matrix_world @ v.co).z for v in evaluated.data.vertices)
rig.location.z += .378-bottom
bpy.context.view_layer.update()

# Fit the cap in rest coordinates, then bind it rigidly to the head bone.
cap_verts, cap_faces = [], []
for k, (z, radius) in enumerate([(1.738,1.0),(1.755,1.04),(1.771,1.04),
                                 (1.801,.92),(1.837,.67),(1.853,.32),(1.856,.02)]):
    for j in range(32):
        a = j*math.tau/32
        cap_verts.append((.091*radius*math.cos(a), .019+.108*radius*math.sin(a), z))
        if k:
            b = (k-1)*32+j
            c = (k-1)*32+(j+1)%32
            cap_faces.append((b,c,c+32,b+32))
cap = mesh('Ribbed watch cap', cap_verts, cap_faces, hat)
cap.parent = rig
group = cap.vertex_groups.new(name='Head')
group.add(list(range(len(cap_verts))), 1.0, 'REPLACE')
mod = cap.modifiers.new('Follow head', 'ARMATURE')
mod.object = rig
for p in cap.data.polygons:
    p.use_smooth = True

world = bpy.data.worlds.new('Blue sky fill')
scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.44,.63,.78,1)
world.node_tree.nodes['Background'].inputs[1].default_value = .38
bpy.ops.object.light_add(type='SUN', location=(-5, -4, 7))
sun = bpy.context.object
sun.name = 'Low afternoon sun'
sun.rotation_euler = Vector((.74,.45,-1)).to_track_quat('-Z','Y').to_euler()
sun.data.energy = 2.35
sun.data.color = (1,.83,.64)
sun.data.angle = math.radians(12)
bpy.ops.object.light_add(type='AREA', location=(2, 2, 6))
fill = bpy.context.object
fill.rotation_euler = (Vector((-2,-2,1))-fill.location).to_track_quat('-Z','Y').to_euler()
fill.data.energy = 180
fill.data.shape = 'DISK'
fill.data.size = 7
fill.data.color = (.72,.87,1)
bpy.ops.object.camera_add(location=(4.8,-9.5,6.1))
camera = bpy.context.object
camera.name = 'Riverbank wide shot'
camera.rotation_euler = (Vector((-1.05,-.55,.43))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 10.2
scene.camera = camera
scene.frame_set(1)
assert scene.camera and scene.frame_end == 48 and body.find_armature() == rig
