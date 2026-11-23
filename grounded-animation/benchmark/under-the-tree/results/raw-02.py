from pathlib import Path
import math
import random

import bpy
from mathutils import Vector

ASSETS = Path(__file__).resolve().parent / "assets"
ENV = ASSETS / "environment"
rng = random.Random(247)
scene = bpy.context.scene
for obj in list(scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start = 1
scene.frame_end = 48
scene.view_settings.view_transform = 'AgX'


def material(name, color, roughness=0.65):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat, bsdf


def mesh(name, verts, faces, materials, indices=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    for mat in materials:
        data.materials.append(mat)
    if indices is not None:
        for poly, index in zip(data.polygons, indices):
            poly.material_index = index
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    return obj


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()


# Tomas, a field worker. Facial topology, rig and grooms adapted from the
# Blender Foundation's Einar rig (CC BY 4.0, studio.blender.org).
with bpy.data.libraries.load(str(ASSETS / "einar.blend"), link=False) as (_, target):
    target.collections = ["CH-einar"]
cast = target.collections[0]
scene.collection.children.link(cast)
rig = bpy.data.objects["RIG-einar"]
rig.animation_data_clear()
for obj in cast.all_objects:
    if obj.name.startswith("WGT-") or obj.name == "GEO-einar_hat":
        obj.hide_render = True

rig.location.z -= 0.62

# Restyle the rig with a blue canvas coat and dark chestnut hair while
# preserving the production maps for weave, strand variation and roughness.
def tint_color(tree, multiplier, amount):
    for shader in [n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED']:
        slot = shader.inputs["Base Color"]
        if slot.is_linked:
            tint = tree.nodes.new('ShaderNodeMixRGB')
            tint.blend_type = 'MULTIPLY'
            tint.inputs[0].default_value = amount
            tint.inputs[2].default_value = (*multiplier, 1)
            tree.links.new(slot.links[0].from_socket, tint.inputs[1])
            tree.links.new(tint.outputs[0], slot)
        else:
            color = slot.default_value[:3]
            slot.default_value = (*(c*(1-amount+m*amount)
                                    for c, m in zip(color, multiplier)), 1)


for name in ("einar.sweater", "einar.jacket.canvas", "einar.jacket.rim"):
    tree = bpy.data.materials[name].node_tree
    tint_color(tree, (.22, .51, .65), .87)
    if name == "einar.jacket.canvas":
        for group in [n for n in tree.nodes if n.type == 'GROUP']:
            tint_color(group.node_tree, (.18, .47, .64), .89)

tint_color(bpy.data.materials["einar.hair"].node_tree, (.41, .34, .33), .86)


def bone_keys(name, channel, keys):
    bone = rig.pose.bones[name]
    for frame, value in keys:
        setattr(bone, channel, value)
        bone.keyframe_insert(channel, frame=frame, group=name)


bone_keys("FK-Head", "rotation_euler", [
    (1, (-0.01, 0.075, -0.035)), (15, (-0.01, 0.075, -0.035)),
    (22, (-0.025, 0.105, -0.035)), (29, (0.012, 0.145, -0.03)),
    (36, (0.041, 0.149, -0.028)), (48, (0.044, 0.142, -0.027)),
])
bone_keys("MSTR-TGT-Eyes", "location", [
    (1, (-0.13, 0, 0.022)), (14, (-0.13, 0, 0.022)),
    (17, (-0.30, 0, 0.084)), (22, (-0.34, 0, 0.035)),
    (28, (-0.38, 0, -0.031)), (34, (-0.40, 0, -0.136)),
    (40, (-0.32, 0, -0.126)), (48, (-0.32, 0, -0.126)),
])
bone_keys("MSTR-Spine_Chest", "location", [
    (1, (0, 0, 0)), (12, (0, .0016, -.0012)),
    (25, (0, 0, 0)), (38, (0, .0014, -.001)), (48, (0, .0004, -.0003)),
])
for side, inward in (('L', -1), ('R', 1)):
    bone_keys("ACT-Eyebrow_Inner." + side, "location", [
        (1, (inward*.002, -.004, 0)), (15, (inward*.002, -.004, 0)),
        (23, (inward*.001, -.0015, 0)), (35, (inward*.001, -.002, 0)),
        (44, (inward*.0008, -.0018, 0)),
    ])
    bone_keys("ACT-Mouth_Corner." + side, "location", [
        (1, (inward*.0013, .0028, 0)), (35, (inward*.0013, .0028, 0)),
        (42, (inward*.0003, .0005, 0)), (48, (inward*.0003, .0005, 0)),
    ])
    bone_keys("Blink." + side, "location", [
        (1, (0, 0, 0)), (33, (0, 0, 0)), (34, (0, -.0025, 0)),
        (35, (0, -.006, 0)), (36, (0, -.003, 0)), (38, (0, 0, 0)),
    ])

# Long portrait lens with a modest depth of field so the eyes and mouth
# remain in focus, with room on the right for the leaf.
bpy.ops.object.camera_add(location=(.50, -1.31, 1.069))
camera = bpy.context.object
camera.name = "Portrait"
aim(camera, (.050, -.014, 1.002))
camera.data.lens = 77
camera.data.dof.use_dof = True
camera.data.dof.focus_distance = (camera.location - Vector((.0, -.126, 1.033))).length
camera.data.dof.aperture_fstop = 8.0
scene.camera = camera

# Build the trunk with flared roots and vertically aligned bark grain.
bark, bark_shader = material("Oak bark", (.16, .09, .042), .88)
nodes = bark.node_tree.nodes
links = bark.node_tree.links
uv = nodes.new('ShaderNodeTexCoord')
for file, color in (("oak_bark_diffuse.jpg", True), ("oak_bark_normal.jpg", False)):
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(ENV / file))
    links.new(uv.outputs["UV"], tex.inputs["Vector"])
    if color:
        links.new(tex.outputs["Color"], bark_shader.inputs["Base Color"])
    else:
        tex.image.colorspace_settings.name = 'Non-Color'
        normal = nodes.new('ShaderNodeNormalMap')
        normal.inputs["Strength"].default_value = 0.85
        links.new(tex.outputs["Color"], normal.inputs["Color"])
        links.new(normal.outputs["Normal"], bark_shader.inputs["Normal"])

verts, faces = [], []
rings, sectors = 28, 80
for ring in range(rings):
    z = -.12 + ring * .123
    for side in range(sectors):
        a = math.tau * side / sectors
        r = (.345 - .020*z + .13*math.exp(-max(0, z)*5)
             + .014*math.sin(9*a + 1.3*z) + .012*math.cos(17*a - .9*z)
             + .009*math.cos(27*a + 2*z) + .026*math.sin(3*a + .5*z))
        verts.append((-.248 - .030*z + r*math.cos(a),
                      .414 + .017*z + r*math.sin(a), z))
for ring in range(rings - 1):
    for side in range(sectors):
        a = ring * sectors + side
        b = ring * sectors + (side+1) % sectors
        faces.append((a, b, b+sectors, a+sectors))
oak = mesh("Old oak", verts, faces, [bark])
bark_uv = oak.data.uv_layers.new(name="Bark grain")
for poly in oak.data.polygons:
    ring, side = divmod(poly.index, sectors)
    for loop, (u, v) in zip(poly.loop_indices, (
        (side, ring), (side+1, ring), (side+1, ring+1), (side, ring+1)
    )):
        bark_uv.data[loop].uv = (2.25*u/sectors, v*.123)
    poly.use_smooth = True


def terrain_z(x, y):
    return .049*y + .15*math.sin(.42*y) + .12*math.sin(.61*x + .45*y)


ground, soil = material("Dry meadow ground", (.21, .20, .08), .96)
tree = ground.node_tree
noise = tree.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 1.9
texcoords = tree.nodes.new("ShaderNodeTexCoord")
tree.links.new(texcoords.outputs["Object"], noise.inputs["Vector"])
ramp = tree.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = .12
ramp.color_ramp.elements[0].color = (.078, .099, .026, 1)
ramp.color_ramp.elements[1].position = .85
ramp.color_ramp.elements[1].color = (.36, .31, .105, 1)
tree.links.new(noise.outputs["Fac"], ramp.inputs[0])
tree.links.new(ramp.outputs[0], soil.inputs["Base Color"])
verts = [(x, y, terrain_z(x, y)) for y in range(-4, 58) for x in range(-32, 33)]
faces = [(j*65+i, j*65+i+1, (j+1)*65+i+1, (j+1)*65+i)
         for j in range(61) for i in range(64)]
mesh("Rolling field", verts, faces, [ground])

greens = [material("Meadow " + name, color)[0] for name, color in (
    ("olive", (.16, .205, .053)), ("straw", (.43, .32, .106)),
    ("sage", (.215, .25, .100)), ("green", (.092, .139, .034)),
    ("seed", (.40, .29, .125)),
)]
# Each strip has a time offset so the gust crosses the frame in a wave.
for strip in range(10):
    verts, faces, indices, offsets = [], [], [], []
    for _ in range(295):
        x = -5.5 + 1.1*(strip + rng.random())
        y = rng.uniform(.68, 16)
        z = terrain_z(x, y)
        for blade in range(rng.randrange(3, 8)):
            angle = rng.uniform(0, math.tau)
            dx, dy = math.cos(angle), math.sin(angle)
            height = rng.uniform(.16, .70) * (1 if y > 2 else .72)
            width = rng.uniform(.009, .025)
            lean = rng.uniform(.075, .25)
            base = len(verts)
            for t, taper in ((0, .58), (.40, 1), (.76, .55), (1, .025)):
                for side in (-1, 1):
                    verts.append((x + dx*lean*t*t - side*dy*width*taper,
                                  y + dy*lean*t*t + side*dx*width*taper,
                                  z + height*t))
                    offsets.append(t*t*height)
            color = rng.randrange(4)
            for i in range(0, 6, 2):
                v = base+i
                faces.append((v, v+1, v+3, v+2))
                indices.append(color)
            if blade == 0 and height > .35:
                v = len(verts)
                tip = Vector((x+dx*lean, y+dy*lean, z+height))
                for side in range(4):
                    a = math.pi*.5*side
                    verts.append(tuple(tip + Vector((.024*math.cos(a), .024*math.sin(a), -.013))))
                    offsets.append(height)
                verts.append(tuple(tip + Vector((.016*dx,.016*dy,.068))))
                offsets.append(height*1.1)
                for i in range(4):
                    faces.append((v+i, v+(i+1)%4, v+4))
                    indices.append(4)

    obj = mesh("Meadow breeze %02d" % strip, verts, faces, greens, indices)
    obj.shape_key_add(name="Still")
    sway = obj.shape_key_add(name="Wind bend")
    for point, (x, y, z), weight in zip(sway.data, verts, offsets):
        point.co = (x+.41*weight, y+.16*weight, z-.085*weight)
    delay = round((9-strip)*.82)
    for frame, strength in ((1,0), (12+delay,0), (18+delay,.88),
                            (24+delay,-.19), (29+delay,.25), (36+delay,0), (48,0)):
        sway.slider_min = -.4
        sway.value = strength
        sway.keyframe_insert(data_path="value", frame=frame)

# Compound lobes, a curved midrib, and color breaks survive the small render.
leaf_mats = [material("Oak leaf " + name, c, .53)[0] for name,c in (
    ("honey", (.67,.28,.041)), ("edge", (.40,.106,.025)),
    ("amber", (.53,.19,.029)), ("rib", (.35,.17,.051)),
)]
outline = [.05,.43,.30,.75,.54,.94,.63,.99,.65,.81,.44,.52,.03]
verts, faces, indices = [], [], []
for row, breadth in enumerate(outline):
    t = row/(len(outline)-1)
    center = .11*math.sin(t*math.pi*1.5)
    arch = .15*math.sin(t*math.pi)
    for side in (-1, -.035, .035, 1):
        verts.append((center + side*breadth*.52, t-.5,
                      arch - abs(side)*breadth*.15 + side*t*.11))
for row in range(len(outline)-1):
    for i in range(3):
        a = row*4+i
        faces.append((a, a+1, a+5, a+4))
        indices.append(3 if i == 1 else rng.choices([0,1,2],[5,1,3])[0])
leaf = mesh("Tracked oak leaf", verts, faces, leaf_mats, indices)

right = camera.rotation_euler.to_matrix().col[0]
up = camera.rotation_euler.to_matrix().col[1]
forward = -camera.rotation_euler.to_matrix().col[2]


def stage_leaf(obj, start, end, sx, ex, distance, length, phase):
    obj.scale = (length,)*3
    for frame in sorted({1, 48, *range(start, min(end, 48)+1, 2), min(end, 48)}):
        t = (frame-start)/(end-start)
        x = sx+(ex-sx)*t + .020*math.sin(t*math.tau*1.35 + phase)
        y = .215 - .425*t + .018*math.sin(t*math.tau + phase)
        obj.location = camera.location + forward*(distance+.105*t) + right*x + up*y
        obj.rotation_euler = (1.1+1.0*math.sin(phase+t*8), .50+t*6+phase,
                              -.50+.60*math.sin(t*9+phase))
        obj.keyframe_insert(data_path="location", frame=frame)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)


stage_leaf(leaf, 10, 43, .149, .194, 1.12, .052, .23)
for number, parameters in enumerate([
    (9, 31, .34, .42, 1.95, .049, 1.2),
    (15, 58, .37, .30, 2.0, .054, 1.7),
    (16, 49, -.35, -.25, 1.25, .034, .9),
    (18, 54, .52, .52, 2.9, .069, 2.7),
    (26, 65, .44, .39, 2.0, .044, 3.4),
    (19, 53, .28, .34, 1.74, .031, 4.5),
    (13, 56, -.46, -.36, 2.12, .055, 2.2),
], 1):
    obj = bpy.data.objects.new("Drifting oak leaf %02d" % number, leaf.data)
    scene.collection.objects.link(obj)
    stage_leaf(obj, *parameters)

# Cool open-sky fill and warm afternoon light skimming the far cheek.
world = bpy.data.worlds.new("Meadow sky")
world.use_nodes = True
scene.world = world
tree = world.node_tree
env = tree.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(str(ENV / "autumn_meadow_1k.hdr"))
tree.links.new(env.outputs["Color"], tree.nodes.get("Background").inputs["Color"])
tree.nodes.get("Background").inputs["Strength"].default_value = .40


def light(name, kind, position, target, energy, color, size):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = color
    if kind == 'AREA':
        data.shape = 'DISK'
        data.size = size
    else:
        data.angle = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    aim(obj, target)
    return obj


light("Open sky above the field", 'AREA', (.65,-1.55,2.40), (0,0,1), 96,
      (.80,.88,1), 2.15)
light("Late light rim", 'AREA', (.85,.72,1.85), (0,0,1.02), 126,
      (1,.76,.48), .98)
light("Sun over the field", 'SUN', (3,5,3.7), (0,0,0), 1.8,
      (1,.83,.60), .13)

for name, frame in (("Under the oak", 1), ("Breeze gathers", 13),
                    ("Eyes find the leaf", 17), ("Quiet again", 33)):
    scene.timeline_markers.new(name, frame=frame)
scene.frame_set(1)
