"""Under the Tree. Run with blender -b --factory-startup -P scene.py."""
from pathlib import Path
from math import cos, sin, pi, exp
from random import Random

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
assets = Path(__file__).resolve().parent / "assets"
env = assets / "environment"
rng = Random(41)

# Einar Rig (CC BY 4.0) Blender Foundation | studio.blender.org
with bpy.data.libraries.load(str(assets / "einar.blend"), link=False) as (_, library):
    library.collections = ["CH-einar"]
    library.actions = ["RIG-Einar_Blink_EyeOpen"]
scene.collection.children.link(library.collections[0])
rig = bpy.data.objects["RIG-einar"]
rig.animation_data_clear()
rig.location.z -= .68
rig.rotation_euler.x = -.09

for suffix in ("hat", "hair.messy", "mustache.messy", "beard.messy"):
    bpy.data.objects["GEO-einar_" + suffix].hide_render = True

# Shorter whiskers give the field worker a different silhouette from the donor groom.
for suffix, length in (("beard", .57), ("mustache", .78)):
    groom = bpy.data.objects["GEO-einar_" + suffix].data
    points = groom.position_data
    offsets = [offset.value for offset in groom.curve_offset_data]
    for start, end in zip(offsets, offsets[1:]):
        root = points[start].vector.copy()
        for i in range(start+1, end):
            points[i].vector = root.lerp(points[i].vector, length)

def material(name, color, roughness=.75):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat, bsdf

def tint(name, color):
    mat = bpy.data.materials[name]
    tree = mat.node_tree
    if name == "einar.jacket.canvas":
        tree = tree.nodes["Group"].node_tree
    nodes, links = tree.nodes, tree.links
    for shader in list(nodes):
        if shader.type != "BSDF_PRINCIPLED":
            continue
        socket = shader.inputs["Base Color"]
        if socket.is_linked:
            source = socket.links[0].from_socket
            mix = nodes.new("ShaderNodeMixRGB")
            mix.blend_type = "MULTIPLY"
            mix.inputs[0].default_value = 1
            mix.inputs[2].default_value = (*color, 1)
            links.new(source, mix.inputs[1])
            links.new(mix.outputs[0], socket)

for name, color in (
    ("einar.hair", (.61, .39, .25)),
    ("eyes.iris", (.73, .83, .46)),
    ("einar.jacket.canvas", (.42, .68, .69)),
    ("einar.jacket.collar", (.44, .68, .67)),
    ("einar.sweater", (.78, .54, .34)),
):
    tint(name, color)

def pose(name, path, keys):
    bone = rig.pose.bones[name]
    if path == "rotation_euler":
        bone.rotation_mode = "XYZ"
    for frame, value in keys:
        setattr(bone, path, value)
        bone.keyframe_insert(path, frame=frame, group=name)

pose("FK-Chest", "rotation_euler", [(1,(0,0,0)), (15,(.009,0,0)), (32,(-.003,0,0)), (48,(.005,0,0))])
pose("FK-Head", "rotation_euler", [(1,(.008,.015,-.035)), (18,(.008,.015,-.035)),
    (27,(.045,-.062,-.02)), (35,(.081,-.092,-.004)), (48,(.076,-.088,-.004))])
pose("MSTR-TGT-Eyes", "location", [(1,(-.032,0,.014)), (14,(-.032,0,.014)),
    (17,(.195,0,.037)), (22,(.218,0,-.04)), (31,(.19,0,-.13)),
    (38,(.139,0,-.105)), (48,(.136,0,-.104))])

for side, sign in (("L", 1), ("R", -1)):
    pose("ACT-Eyebrow_Inner."+side, "location", [(1,(-sign*.0018,-.0017,0)),
        (22,(-sign*.0018,-.0017,0)), (33,(-sign*.0011,-.001,0)), (44,(0,-.0004,0))])
    pose("ACT-Mouth_Corner."+side, "location", [(1,(-sign*.0008,.0016,0)),
        (34,(-sign*.0008,.0016,0)), (43,(sign*.0003,.00025,0)), (48,(sign*.0003,.00025,0))])
pose("MSTR-Jaw", "rotation_euler", [(1,(0,0,0)), (34,(0,0,0)), (43,(.013,0,0)), (48,(.012,0,0))])

# Use the rig's fitted eyelid shape at the closed pose.
blink = library.actions[0]
channels = blink.layers[0].strips[0].channelbags[0].fcurves
for curve in channels:
    if not curve.data_path.startswith(('pose.bones["Blink.', 'pose.bones["Eyelid_')):
        continue
    rest, closed = curve.evaluate(10), curve.evaluate(20)
    if abs(closed-rest) < 1e-6:
        continue
    bone_path, prop = curve.data_path.rsplit(".", 1)
    bone = rig.path_resolve(bone_path)
    for frame, amount in ((34,0), (35,.56), (36,1), (37,.35), (39,0)):
        getattr(bone, prop)[curve.array_index] = rest + (closed-rest)*amount
        bone.keyframe_insert(prop, index=curve.array_index, frame=frame, group=bone.name)

def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    data.materials.append(mat)
    for polygon in data.polygons:
        polygon.use_smooth = True
    return obj

def aim(obj, point):
    obj.rotation_euler = (Vector(point)-obj.location).to_track_quat("-Z", "Y").to_euler()

cam = bpy.data.objects.new("Close-up", bpy.data.cameras.new("Portrait lens"))
scene.collection.objects.link(cam)
cam.location = (.345,-.805,1.00)
aim(cam, (-.080,-.035,.958))
cam.data.lens = 61
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = .78
cam.data.dof.aperture_fstop = 7.1
scene.camera = cam
bpy.context.view_layer.update()

bark, bark_bsdf = material("Weathered oak", (.19,.12,.065), .88)
nodes, links = bark.node_tree.nodes, bark.node_tree.links
uv = nodes.new("ShaderNodeTexCoord")
normal = nodes.new("ShaderNodeNormalMap")
normal.inputs["Strength"].default_value = .83
for kind in ("diffuse", "normal"):
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(env / ("oak_bark_" + kind + ".jpg")))
    links.new(uv.outputs["UV"], tex.inputs["Vector"])
    if kind == "diffuse":
        links.new(tex.outputs["Color"], bark_bsdf.inputs["Base Color"])
    else:
        tex.image.colorspace_settings.name = "Non-Color"
        links.new(tex.outputs["Color"], normal.inputs["Color"])
links.new(normal.outputs[0], bark_bsdf.inputs["Normal"])

def wood(name, base, tip, radius, end_radius):
    base, tip = Vector(base), Vector(tip)
    axis = tip-base
    rotation = axis.to_track_quat("Z","Y")
    n, rows = 96, 29
    verts, faces = [], []
    for row in range(rows):
        t = row/(rows-1)
        for j in range(n):
            a = 2*pi*j/n
            r = (radius*(1-t)+end_radius*t)*(1+.09*sin(5*a+2*t)+.035*sin(21*a+4*t))
            r += .012*sin(47*a+1.6*sin(8*t+a))
            verts.append(base+t*axis+rotation@Vector((r*cos(a)+.045*sin(t*pi),r*sin(a),0)))
    for i in range(rows-1):
        for j in range(n):
            k = (j+1)%n
            faces.append((i*n+j,i*n+k,(i+1)*n+k,(i+1)*n+j))
    obj = mesh(name, verts, faces, bark)
    layer = obj.data.uv_layers.new()
    for p in obj.data.polygons:
        i,j = divmod(p.index,n)
        for l,(x,y) in zip(p.loop_indices, ((j,i),(j+1,i),(j+1,i+1),(j,i+1))):
            layer.data[l].uv = (x/n*radius*8,y/(rows-1)*axis.length*2)
    return obj

wood("Oak trunk", (.08,.48,-.11), (.09,.43,4.9), .395,.30)
wood("Low branch", (.09,.44,2.45), (-2.5,.28,4.3), .18,.047)

ground, soil = material("Meadow earth", (.22,.23,.07))
nodes, links = ground.node_tree.nodes, ground.node_tree.links
noise = nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 1.6
coord = nodes.new("ShaderNodeTexCoord")
links.new(coord.outputs["Object"],noise.inputs["Vector"])
ramp = nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = .23
ramp.color_ramp.elements[0].color = (.065,.09,.022,1)
ramp.color_ramp.elements[1].position = .82
ramp.color_ramp.elements[1].color = (.38,.32,.095,1)
links.new(noise.outputs["Fac"],ramp.inputs[0])
links.new(ramp.outputs[0],soil.inputs["Base Color"])

def height(x,y):
    d = max(0,y-.4)
    return .61*(1-exp(-d*.34))+.11*sin(x*.44+y*.37)*(1-exp(-d))

verts = [(i*.65,j*.65,height(i*.65,j*.65)) for j in range(-6,61) for i in range(-45,46)]
mesh("Rolling field", verts,
     [(j*91+i,j*91+i+1,(j+1)*91+i+1,(j+1)*91+i) for j in range(66) for i in range(90)], ground)

bpy.ops.import_scene.gltf(filepath=str(env / "grass/grass_medium_01_1k.gltf"))
tufts = [o for o in bpy.context.selected_objects if o.type == "MESH"]
assert tufts, "Grass import produced no mesh"
for source in tufts:
    source.hide_render = True
    source.hide_set(True)
for i in range(520):
    source = rng.choice(tufts)
    plant = bpy.data.objects.new("Meadow grass",source.data)
    scene.collection.objects.link(plant)
    y = rng.uniform(.85,5.4) if i < 240 else rng.uniform(5,21)
    x = rng.uniform(-.82*y-3,-.16*y+.5)
    plant.location = (x,y,height(x,y)-.01)
    scale = rng.uniform(.8,1.85)
    plant.scale = (scale,scale,scale*rng.uniform(.8,1.4))
    angle = rng.uniform(0,2*pi)
    delay = round(min(9,max(0,(-x-.6)*1.65)))
    for frame,bend in ((1,0),(12+delay,.015),(18+delay,.25),(22+delay,-.064),
                       (26+delay,.15),(32+delay,.025),(38+delay,0),(48,0)):
        plant.rotation_euler = (bend*.43,bend,angle)
        plant.keyframe_insert("rotation_euler", frame=frame)

leaf_mats = []
for color in ((.49,.157,.024),(.63,.29,.042),(.28,.24,.038),(.37,.09,.025)):
    mat, shader = material("Dry oak leaf",color,.61)
    shader.inputs["Subsurface Weight"].default_value = .065
    leaf_mats.append(mat)
rib, _ = material("Leaf midrib",(.34,.18,.056))
edges = [0,.31,.44,.78,.53,1,.58,.82,.38,.48,0]
leaf_path = [(1,-.169,.157),(13,-.163,.132),(17,-.147,.083),(23,-.172,.048),
             (29,-.199,.006),(36,-.182,-.055),(43,-.201,-.129),(48,-.217,-.171)]
for i in range(10):
    size = .047 if i == 0 else rng.uniform(.034,.071)
    vertices = []
    for j, edge in enumerate(edges):
        t = j/(len(edges)-1)
        w = size*.3*edge + .00012
        h = size*.12*sin(pi*t)
        vertices.extend([(-w,t*size,h-w*.25),(-.00037,t*size,h),
                         (.00037,t*size,h),(w,t*size,h-w*.25)])
    leaf = mesh("Falling oak leaf",vertices,
                [(4*j+k,4*j+k+1,4*j+k+5,4*j+k+4) for j in range(10) for k in range(3)],
                leaf_mats[i % len(leaf_mats)])
    leaf.data.materials.append(rib)
    for p in leaf.data.polygons:
        if p.index%3 == 1:
            p.material_index = 1
    depth = .65 if i == 0 else rng.uniform(1.17,2.8)
    start_x, drift = rng.uniform(-.45,-.16), rng.uniform(-.14,.11)
    z, speed = rng.uniform(.17,.69), rng.uniform(.21,.52)
    phase = rng.uniform(-pi,pi)
    for f,x,h in leaf_path:
        t = (f-1)/47
        if i:
            x = start_x + drift*t + .045*sin(phase+t*9)
            h = z-speed*t+.019*sin(phase+t*12)
        else:
            x, h = .64*x, .775*h
        leaf.location = cam.matrix_world @ Vector((x,h,-depth))
        leaf.rotation_euler = (1.15+.71*sin(phase+t*13), .43*cos(phase+t*18), phase+t*(3.7+i*.48))
        leaf.keyframe_insert("location",frame=f)
        leaf.keyframe_insert("rotation_euler",frame=f)

world = scene.world = bpy.data.worlds.new("Late afternoon sky")
world.use_nodes = True
nodes, links = world.node_tree.nodes, world.node_tree.links
sky = nodes.new("ShaderNodeTexEnvironment")
sky.image = bpy.data.images.load(str(env/"autumn_meadow_1k.hdr"))
background = nodes.get("Background")
links.new(sky.outputs["Color"],background.inputs[0])
background.inputs["Strength"].default_value = .43

def light(name, kind, location, energy, color, size, target):
    data = bpy.data.lights.new(name,kind)
    obj = bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    obj.location = location
    data.energy, data.color = energy,color
    data.use_shadow = name in ("Low sun over the field", "Open sky in front")
    if kind == "SUN":
        data.angle = size
    else:
        data.shape, data.size = "DISK",size
    aim(obj,target)

light("Low sun over the field","SUN",(-4,3,4),2.0,(1,.81,.58),.075,(0,0,.8))
light("Open sky in front","AREA",(-1.4,-2.2,2.9),95,(.75,.85,1),2.6,(0,0,1))
light("Field bounce","AREA",(1,-.68,1.2),12,(1,.83,.65),1.3,(0,0,1))
light("Canopy edge","AREA",(-.9,.52,1.85),28,(1,.71,.43),.75,(0,0,1.06))

scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 32
scene.render.resolution_x,scene.render.resolution_y = 640,360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start,scene.frame_end = 1,48
scene.view_settings.view_transform = "AgX"
scene.frame_set(1)
assert scene.camera == cam and rig.animation_data.action and scene.frame_end == 4*scene.render.fps
