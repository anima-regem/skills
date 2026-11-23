"""Under the Tree. Run with Blender in background mode and autoexec disabled."""
from pathlib import Path
import math
import random

import bpy
from mathutils import Euler, Vector, noise

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ENV = ASSETS / "environment"
rng = random.Random(71)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'

credits = bpy.data.texts.new("Asset credits")
credits.write("""Einar Rig (CC BY 4.0) Blender Foundation | studio.blender.org
https://studio.blender.org/characters/einar/v1/
https://creativecommons.org/licenses/by/4.0/
Supplied close-up edition, adapted with a new face sculpt, coloring, pose and animation.
Jolcham Oak Bark 01 by Charlotte Baglioni, Grass Medium 01 by Poly Haven,
and Autumn Meadow by Sergej Majboroda, CC0.
https://polyhaven.com/a/jolcham_oak_bark_01
https://polyhaven.com/a/grass_medium_01
https://polyhaven.com/a/autumn_meadow
""")
with bpy.data.libraries.load(str(ASSETS / "einar.blend"), link=False) as (_, out):
    out.collections = ["CH-einar"]
character = out.collections[0]
scene.collection.children.link(character)
rig = bpy.data.objects["RIG-einar"]
rig.animation_data_clear()
rig.location.z = -.665
rig['character'] = "Alden"
for ob in character.all_objects:
    if ob.name.startswith("WGT-"):
        ob.hide_render = True

# Multiply the original texture signals to retain weave and wear.
def tint(mat_name, color):
    mat = bpy.data.materials.get(mat_name)
    if not mat or not mat.use_nodes:
        return
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for shader in [node for node in nodes if node.type == 'BSDF_PRINCIPLED']:
        base = shader.inputs['Base Color']
        if base.is_linked:
            original = base.links[0].from_socket
            mul = nodes.new('ShaderNodeMixRGB')
            mul.blend_type = 'MULTIPLY'
            mul.inputs[0].default_value = 1
            mul.inputs[2].default_value = (*color, 1)
            links.new(original, mul.inputs[1])
            links.new(mul.outputs[0], base)
        else:
            old = tuple(base.default_value)
            base.default_value = (*(a*b for a, b in zip(old, color)), 1)

for name in ("einar.jacket.canvas", "einar.jacket.rim", "einar.jacket.collar"):
    tint(name, (.34, .68, .66))
tint("einar.hat", (.42, .53, .60))
tint("einar.sweater", (.71, .55, .39))
tint("eyes.iris", (.76, .93, .67))

# A subtly hooked, broader bridge gives Alden his own profile while
# leaving the tip, eyelids and mouth available to the production rig.
head = bpy.data.objects["GEO-einar_head"]
identity = head.shape_key_add(name="Alden face", from_mix=False)
for point in identity.data:
    x, y, z = point.co
    mask = math.exp(-((x/.019)**2 + ((z-1.644)/.016)**2
                      + ((y+.148)/.022)**2))
    point.co.x += x*.25*mask
    point.co.y -= .012*mask
    point.co.z -= .0025*mask
identity.value = 1

def pose(name, channel, keys):
    bone = rig.pose.bones[name]
    if channel == 'rotation_euler':
        bone.rotation_mode = 'XYZ'
    for frame, value in keys:
        setattr(bone, channel, value)
        bone.keyframe_insert(data_path=channel, frame=frame, group=name)

pose("FK-Chest", 'rotation_euler',
     [(1,(-.09,0,-.035)), (12,(-.086,0,-.035)), (25,(-.093,0,-.035)),
      (36,(-.086,0,-.035)), (48,(-.09,0,-.035))])
pose("FK-Head", 'rotation_euler',
     [(1,(.079,-.075,-.014)), (16,(.079,-.075,-.014)),
      (20,(.076,-.060,-.014)), (29,(.091,.027,.006)),
      (36,(.107,.041,.012)), (48,(.108,.039,.009))])
pose("MSTR-TGT-Eyes", 'location',
     [(1,(.018,0,.027)), (12,(.018,0,.027)), (16,(-.233,0,.115)),
      (22,(-.257,0,.066)), (29,(-.217,0,-.018)),
      (35,(-.182,0,-.059)), (48,(-.163,0,-.065))])
for side, sign in [('L', 1), ('R', -1)]:
    pose("ACT-Eyebrow_Inner."+side, 'location',
         [(1,(-sign*.0023,-.0034,0)), (21,(-sign*.0020,-.003,0)),
          (36,(-sign*.0015,-.0017,0)), (48,(-sign*.0012,-.0014,0))])
    pose("ACT-Eyebrow_Outer."+side, 'location',
         [(1,(0,.0008*sign,0)), (23,(0,.0015*sign,0)), (48,(0,.0003,0))])
    pose("Blink."+side, 'location',
         [(1,(0,0,0)), (32,(0,0,0)), (34,(0,-.006,0)),
          (35,(0,-.0026,0)), (37,(0,0,0)), (48,(0,0,0))])
    pose("ACT-Mouth_Corner."+side, 'location',
         [(1,(-sign*.0024,.0013,0)), (32,(-sign*.0024,.0013,0)),
          (40,(-sign*.00035,.00015,0)), (48,(-sign*.00035,.00015,0))])
pose("MSTR-Jaw", 'rotation_euler',
     [(1,(.009,0,0)), (33,(.009,0,0)), (42,(-.008,0,0)), (48,(-.008,0,0))])

def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

camera = bpy.data.objects.new("Locked portrait camera", bpy.data.cameras.new("Portrait 73 mm"))
scene.collection.objects.link(camera)
camera.location = (-.465,-.97,1.075)
aim(camera, (.079,-.015,.976))
camera.data.lens = 73
camera.data.dof.use_dof = True
camera.data.dof.focus_distance = (camera.location - Vector((0,-.137,1.015))).length
camera.data.dof.aperture_fstop = 5.6
scene.camera = camera

def material(name, color, roughness=.65):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color,1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = (*color,1)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat, bsdf

def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    data.materials.append(mat)
    return ob

bark, bsdf = material("Jolcham oak", (.19,.11,.062), .91)
for name, is_normal in [('oak_bark_diffuse.jpg', False), ('oak_bark_normal.jpg', True)]:
    node = bark.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = bpy.data.images.load(str(ENV / name))
    if is_normal:
        node.image.colorspace_settings.name = 'Non-Color'
        normal = bark.node_tree.nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value = 1.12
        bark.node_tree.links.new(node.outputs['Color'], normal.inputs['Color'])
        bark.node_tree.links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
    else:
        bark.node_tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])

sides, rings = 96, 37
verts, faces = [], []
for row in range(rings):
    z = row*.126
    for col in range(sides):
        a = 2*math.pi*col/sides
        radius = (.34 - .036*z + .16*math.exp(-z*5)
                  + .031*math.sin(7*a + z*.9) + .019*math.sin(13*a-z*1.2)
                  + .016*noise.noise_vector((math.cos(a)*6, math.sin(a)*6, z*1.7))[1])
        verts.append((-.135 + .022*z + radius*math.cos(a),
                      .422 + .017*z + radius*math.sin(a), z-.035))
for row in range(rings-1):
    for col in range(sides):
        a, b = row*sides+col, row*sides+(col+1)%sides
        faces.append((a,b,b+sides,a+sides))
trunk = mesh("Oak at the field edge", verts, faces, bark)
uv = trunk.data.uv_layers.new()
for p in trunk.data.polygons:
    p.use_smooth = True
    y, x = divmod(p.index,sides)
    for ix, (u,v) in zip(p.loop_indices, [(x,y),(x+1,y),(x+1,y+1),(x,y+1)]):
        uv.data[ix].uv = (u/sides*2.3, v*.126/1.10)

earth, bsdf = material("Dry meadow floor", (.23,.195,.07), .98)
nodes, links = earth.node_tree.nodes, earth.node_tree.links
tex = nodes.new('ShaderNodeTexNoise')
tex.inputs['Scale'].default_value = 2.8
tex.inputs['Detail'].default_value = 4
links.new(nodes.new('ShaderNodeTexCoord').outputs['Object'], tex.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .17
ramp.color_ramp.elements[0].color = (.076,.068,.025,1)
ramp.color_ramp.elements[1].position = .81
ramp.color_ramp.elements[1].color = (.34,.30,.112,1)
links.new(tex.outputs['Fac'], ramp.inputs[0])
links.new(ramp.outputs[0], bsdf.inputs['Base Color'])
mesh("Open field", [(-22,-18,0),(34,-18,0),(34,26,0),(-22,26,0)],
     [(0,1,2,3)], earth)

before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(ENV / "grass/grass_medium_01_1k.gltf"))
imported = [o for o in bpy.data.objects if o not in before]
bpy.context.view_layer.update()
variants = []
for source in sorted((o for o in imported if o.type == 'MESH'), key=lambda o:o.name):
    bounds = [source.matrix_world @ Vector(p) for p in source.bound_box]
    height = max(v.z for v in bounds) - min(v.z for v in bounds)
    variants.append((source.data, height, source.matrix_world.to_quaternion()))
variants = variants[::3]
for o in imported:
    bpy.data.objects.remove(o, do_unlink=True)

# The expanding pulse reaches near clumps first. Every pivot is at soil level.
for i in range(78):
    y = rng.uniform(.68,8.5)
    x = .48*y + rng.uniform(-.6, 2.65)
    grass_data, grass_height, grass_basis = variants[i % len(variants)]
    ob = bpy.data.objects.new(f'Meadow tuft {i+1:02d}', grass_data)
    scene.collection.objects.link(ob)
    ob.location = (x,y,.005)
    scale = rng.uniform(.29,.66)/grass_height
    if i < 12:
        ob.location = (rng.uniform(1.13,2.52),rng.uniform(2.4,4.16),.005)
        scale = rng.uniform(.36,.68)/grass_height
    ob.scale = (scale,)*3
    yaw = rng.uniform(0, 2*math.pi)
    for f in range(1,49,2):
        travel = (f-13)*.43 - ob.location.x*.82 - ob.location.y*.43
        gust = math.exp(-((travel-2.2)/2.5)**2)
        sway = .022*math.sin(f*.48+i) + gust*(.23+.12*math.sin(travel*2.1+i*.24))
        ob.rotation_euler = (Euler((sway*.32, sway, yaw)).to_quaternion() @ grass_basis).to_euler()
        ob.keyframe_insert(data_path='rotation_euler', frame=f)
    ob.keyframe_insert(data_path='rotation_euler', frame=48)

world = bpy.data.worlds.new("Autumn meadow sky")
scene.world = world
world.use_nodes = True
nodes, links = world.node_tree.nodes, world.node_tree.links
hdri = nodes.new('ShaderNodeTexEnvironment')
hdri.image = bpy.data.images.load(str(ENV / 'autumn_meadow_1k.hdr'))
links.new(hdri.outputs['Color'], nodes.get("Background").inputs['Color'])
nodes.get("Background").inputs['Strength'].default_value = .48

def light(name, kind, at, target, color, power, size):
    data = bpy.data.lights.new(name, kind)
    data.color = color
    data.energy = power
    if kind == 'SUN':
        data.angle = size
    else:
        data.shape = 'DISK'
        data.size = size
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    ob.location = at
    aim(ob,target)
    return ob

light("Afternoon sun", 'SUN', (1.7,2.5,2.42), (0,0,.96), (1,.74,.44), 2.15, .15)
light("Open sky under canopy", 'AREA', (.55,-1.32,1.85), (0,-.085,1), (.77,.86,1), 53, 1.38)
light("Field bounce", 'AREA', (-.62,-.96,.60), (0,-.02,.98), (1,.80,.57), 13, 1.04)
light("Sun on leaf edges", 'AREA', (1.29,.1,1.79), (.04,-.1,1.04), (1,.69,.35), 29, .37)

# Lobed oak blades, curled away from their midribs.
def oak_leaf(name, length, color):
    mat, bsdf = material(name, color, .60)
    bsdf.inputs['Subsurface Weight'].default_value = .12
    bsdf.inputs['Subsurface Radius'].default_value = (1,.48,.19)
    bsdf.inputs['Subsurface Scale'].default_value = .003
    vn, _ = material(name+" veins", tuple(v*.66 for v in color))
    outline = [(.0,.015),(.10,.14),(.20,.13),(.28,.25),(.35,.27),
               (.42,.16),(.51,.31),(.59,.29),(.64,.16),(.72,.26),
               (.80,.21),(.84,.12),(.93,.13),(1,.008)]
    verts, faces = [], []
    for t,w in outline:
        z = .20*(t-.46)**2
        verts.extend([(length*x,length*(t-.5),length*(z+dz)) for x,dz in
                      [(-w,.32*w),(0,0),(w*.88,.39*w)]])
    for k in range(0,len(verts)-3,3):
        faces.extend([(k,k+1,k+4,k+3),(k+1,k+2,k+5,k+4)])
    ob = mesh(name, verts, faces, mat)
    ob.data.materials.append(vn)
    for p in ob.data.polygons:
        p.use_smooth = True
    vein = bpy.data.curves.new(name+" midrib", 'CURVE')
    vein.dimensions = '3D'
    vein.bevel_depth = length*.009
    vein.bevel_resolution = 2
    path = [(0,length*(t-.5),length*(.20*(t-.46)**2+.008))
            for t in [-.14,.04,.23,.45,.67,.89,.98]]
    spline = vein.splines.new('POLY')
    spline.points.add(len(path)-1)
    for point, co in zip(spline.points,path):
        point.co = (*co,1)
    rib = bpy.data.objects.new(vein.name,vein)
    scene.collection.objects.link(rib)
    vein.materials.append(vn)
    rib.parent = ob
    return ob

bpy.context.view_layer.update()
right = camera.matrix_world.to_quaternion() @ Vector((1,0,0))
up = camera.matrix_world.to_quaternion() @ Vector((0,1,0))
forward = camera.matrix_world.to_quaternion() @ Vector((0,0,-1))
half_width = camera.data.sensor_width / (2*camera.data.lens)

# Each trajectory is staged in camera space and converted to a world-space fall.
# The leading leaf stays in the open field side of the composition.
falls = [
    ("Leaf he follows", 11, .728, 1.10, .031, .030, 1.04, .037, (.53,.172,.024)),
    ("Copper leaf beyond", 12, .909, 1.12, .040, .023, 1.65, .067, (.43,.108,.014)),
    ("Amber leaf beyond", 19, .837, 1.12, -.016, .019, 2.12, .080, (.50,.239,.042)),
    ("Small red leaf", 22, .973, 1.08, -.029, .027, 1.27, .034, (.41,.082,.021)),
    ("Distant gold leaf", 28, .790, 1.09, .019, .022, 2.65, .074, (.44,.219,.027)),
    ("Late leaf", 31, .933, 1.04, .012, .026, 1.85, .057, (.52,.169,.022)),
]
for i,(name,start,u,v,drift,speed,depth,size,color) in enumerate(falls):
    ob = oak_leaf(name,size,color)
    for f in range(1,49):
        t = f-start
        x = u+drift*t/22+.026*math.sin(t*.25+i)
        y = v-speed*t+.038*math.sin(t*.31+i)
        d = depth + .047*math.sin(t*.21+i) + .002*t
        ob.location = (camera.location + forward*d + right*((2*x-1)*d*half_width)
                       + up*((2*y-1)*d*half_width*9/16))
        ob.rotation_euler = (1.04 + .76*math.sin(t*.245+i),
                             .76*math.sin(t*.176+i), t*.155+i*.95)
        ob.keyframe_insert(data_path='location',frame=f)
        ob.keyframe_insert(data_path='rotation_euler',frame=f)

for label, frame in [('Watching',1),('Breeze gathers',13),('Breeze fades',32),('Hold',40)]:
    scene.timeline_markers.new(label, frame=frame)
scene.frame_set(1)
# Pack images so saving the built scene anywhere preserves its dependencies.
for img in bpy.data.images:
    if img.source == 'FILE' and not img.packed_file and Path(bpy.path.abspath(img.filepath)).is_file():
        img.pack()
