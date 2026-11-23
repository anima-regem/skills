from pathlib import Path
import math
import random

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
ENV = ROOT / "assets" / "environment"
rng = random.Random(81)
sin, cos, pi = math.sin, math.cos, math.pi
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

with bpy.data.libraries.load(str(ROOT / "assets" / "einar.blend")) as (_, dst):
    dst.collections = ["CH-einar"]
scene.collection.children.link(dst.collections[0])
scene["Character attribution"] = "Adapted from Einar by Blender Foundation, CC BY 4.0"
scene["Environment attribution"] = "Jolcham Oak Bark and Autumn Meadow, Poly Haven, CC0"
rig = bpy.data.objects["RIG-einar"]
if rig.animation_data:
    rig.animation_data.action = None
    for track in rig.animation_data.nla_tracks:
        track.mute = True
for obj in dst.collections[0].all_objects:
    if not obj.parent and not obj.name.startswith("WGT-"):
        obj.location.z -= .58
    if obj.name.startswith("WGT-") or obj.name.endswith(".messy"):
        obj.hide_render = True

def material(name, color, roughness=.7):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return mat, shader

# Restyle the supplied facial rig as a silver-haired field worker.
hair, shader = material("Salt and pepper hair", (.10, .075, .055), .49)
info = hair.node_tree.nodes.new("ShaderNodeHairInfo")
ramp = hair.node_tree.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = .30
ramp.color_ramp.elements[0].color = (.031, .023, .018, 1)
ramp.color_ramp.elements[1].position = .85
ramp.color_ramp.elements[1].color = (.39, .32, .25, 1)
hair.node_tree.links.new(info.outputs["Random"], ramp.inputs[0])
hair.node_tree.links.new(ramp.outputs[0], shader.inputs["Base Color"])
for name in ("hair", "beard", "mustache", "eyebrows"):
    bpy.data.objects[f"GEO-einar_{name}"].data.materials[0] = hair

for name in ("einar.jacket.canvas", "einar.jacket.collar", "einar.jacket.rim", "einar.hat"):
    mat = bpy.data.materials.get(name)
    if mat is None:
        continue
    cloth_color = (.25, .115, .049, 1) if name == "einar.hat" else (.07, .20, .18, 1)
    for shader in [n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]:
        socket = shader.inputs["Base Color"]
        if socket.is_linked:
            tree = mat.node_tree
            prior = socket.links[0].from_socket
            tint = tree.nodes.new("ShaderNodeMixRGB")
            tint.blend_type = "COLOR"
            tint.inputs[0].default_value = .87
            tint.inputs[2].default_value = cloth_color
            tree.links.new(prior, tint.inputs[1])
            tree.links.new(tint.outputs[0], socket)
        else:
            socket.default_value = cloth_color

def pose(name, channel, keys):
    bone = rig.pose.bones[name]
    if channel == "rotation_euler":
        bone.rotation_mode = "XYZ"
    for frame, value in keys:
        setattr(bone, channel, value)
        bone.keyframe_insert(channel, frame=frame, group=name)

pose("MSTR-TGT-Eyes", "location", [
    (1, (.055, 0, .025)), (12, (.055, 0, .025)), (16, (-.135, 0, .100)),
    (22, (-.206, 0, .051)), (31, (-.245, 0, -.038)), (39, (-.217, 0, -.078)),
    (48, (-.217, 0, -.078)),
])
pose("FK-Head", "rotation_euler", [
    (1, (.014, -.055, -.047)), (17, (.016, -.054, -.047)),
    (24, (.018, .018, -.025)), (32, (-.027, .061, -.010)),
    (42, (-.039, .062, -.009)), (48, (-.039, .062, -.009)),
])
pose("MSTR-Spine_Torso", "rotation_euler", [
    (1, (.022, 0, -.033)), (15, (.025, 0, -.033)), (32, (.020, 0, -.032)),
    (48, (.023, 0, -.033)),
])
for side, sign in (("L", 1), ("R", -1)):
    pose("Blink." + side, "location", [
        (1, (0, 0, 0)), (34, (0, 0, 0)), (36, (0, -.006, 0)),
        (38.5, (0, 0, 0)), (48, (0, 0, 0)),
    ])
    pose("Eyelid_Upper." + side, "location", [
        (1, (0, 0, 0)), (34, (0, 0, 0)), (36, (0, -.005, 0)),
        (38.5, (0, 0, 0)), (48, (0, 0, 0)),
    ])
    pose("ACT-Eyebrow_Inner." + side, "location", [
        (1, (-sign*.0016, -.0027, 0)), (13, (-sign*.0016, -.0027, 0)),
        (19, (-sign*.001, -.0005, 0)), (31, (-sign*.001, -.001, 0)),
        (48, (-sign*.0004, -.0004, 0)),
    ])
    pose("ACT-Mouth_Corner." + side, "location", [
        (1, (-sign*.0016, sign*.0010, 0)), (34, (-sign*.0016, sign*.0010, 0)),
        (42, (sign*.0002, 0, 0)), (48, (sign*.0002, 0, 0)),
    ])

def mesh_object(name, vertices, faces, materials):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    for mat in materials:
        mesh.materials.append(mat)
    return obj

def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

cam_data = bpy.data.cameras.new("Portrait lens")
cam = bpy.data.objects.new("Locked three-quarter close-up", cam_data)
scene.collection.objects.link(cam)
cam.location = (-.48, -1.19, 1.15)
aim(cam, (.116, -.050, 1.072))
cam_data.lens = 58
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = 1.17
cam_data.dof.aperture_fstop = 4.5
scene.camera = cam

bark, shader = material("Oak bark", (.17, .10, .047), .86)
nodes, links = bark.node_tree.nodes, bark.node_tree.links
diffuse = nodes.new("ShaderNodeTexImage")
diffuse.image = bpy.data.images.load(str(ENV / "oak_bark_diffuse.jpg"))
links.new(diffuse.outputs["Color"], shader.inputs["Base Color"])
normal = nodes.new("ShaderNodeTexImage")
normal.image = bpy.data.images.load(str(ENV / "oak_bark_normal.jpg"))
normal.image.colorspace_settings.name = "Non-Color"
bump = nodes.new("ShaderNodeNormalMap")
bump.inputs["Strength"].default_value = .85
links.new(normal.outputs["Color"], bump.inputs["Color"])
links.new(bump.outputs[0], shader.inputs["Normal"])

def trunk(name, path, sides):
    verts, faces = [], []
    for j, (x, y, z, radius) in enumerate(path):
        for i in range(sides):
            angle = i * 2*pi / sides
            ridge = 1 + .059*sin(7*angle + .31*j) + .036*cos(13*angle - .27*j)
            verts.append((x + radius*ridge*cos(angle), y + radius*ridge*sin(angle), z))
    for j in range(len(path)-1):
        for i in range(sides):
            a, b = j*sides+i, j*sides+(i+1)%sides
            faces.append((a, b, b+sides, a+sides))
    obj = mesh_object(name, verts, faces, [bark])
    uv = obj.data.uv_layers.new()
    for poly in obj.data.polygons:
        j, i = divmod(poly.index, sides)
        u = i * 2.5 / sides
        v0, v1 = path[j][2]*1.4, path[j+1][2]*1.4
        for loop, value in zip(poly.loop_indices, [(u,v0),(u+2.5/sides,v0),(u+2.5/sides,v1),(u,v1)]):
            uv.data[loop].uv = value
        poly.use_smooth = True

trunk("Oak at the field edge", [
    (-.35,.33,-.15,.55),(-.34,.34,.17,.45),(-.33,.35,.51,.39),
    (-.35,.35,.91,.36),(-.41,.36,1.35,.346),(-.44,.37,1.81,.334),
    (-.43,.36,2.40,.31),(-.50,.38,3.02,.27),(-.67,.44,3.85,.22),
    (-.87,.55,4.75,.14),
], 88)
trunk("Fork above the sitter", [
    (-.44,.38,2.32,.21),(-.26,.45,2.77,.19),(.03,.62,3.24,.15),
    (.51,.75,3.64,.12),(1.11,.88,4.02,.075),(1.57,1.10,4.35,.02),
], 45)

def land(x,y):
    return .105*max(0, min(9, y-.2)) + .065*sin(.67*x+.39*y) + .029*cos(1.12*y)

soil, shader = material("Dry meadow earth", (.17,.122,.052), .94)
tex = soil.node_tree.nodes.new("ShaderNodeTexNoise")
tex.inputs["Scale"].default_value = 3.4
color = soil.node_tree.nodes.new("ShaderNodeValToRGB")
color.color_ramp.elements[0].color = (.052,.062,.022,1)
color.color_ramp.elements[1].color = (.36,.26,.085,1)
soil.node_tree.links.new(tex.outputs["Fac"], color.inputs[0])
soil.node_tree.links.new(color.outputs[0], shader.inputs["Base Color"])
verts = [(x,y,land(x,y)) for y in range(-3, 46) for x in range(-28, 35)]
faces = [(j*63+i,j*63+i+1,(j+1)*63+i+1,(j+1)*63+i) for j in range(48) for i in range(62)]
mesh_object("Rolling meadow", verts, faces, [soil])

grass_mats = [material("Meadow blade %02d" % i, c)[0] for i,c in enumerate([
    (.105,.144,.031),(.22,.26,.058),(.32,.315,.079),(.46,.35,.116),
    (.085,.124,.029),(.52,.397,.151),(.30,.35,.09),
])]
for band in range(18):
    verts, faces, shades, heights = [], [], [], []
    origin = band*.64
    for k in range(430):
        y = rng.uniform(.65, 17)
        x = origin + .46*y + rng.uniform(-.45,.32)
        z = land(x,y) - .017
        height = rng.uniform(.12,.52) * (1 + .32*sin(2*x+y))
        for blade in range(5):
            a = rng.uniform(0,2*pi)
            dx,dy = cos(a),sin(a)
            h = height*rng.uniform(.55,1.4)
            w = rng.uniform(.009,.023)
            lean = rng.uniform(.065,.22)
            idx = len(verts)
            for t in (0,.42,.74,1):
                center = (x+dx*lean*t*t, y+dy*lean*t*t, z+h*t)
                width = w*(1-.97*t)*.5
                for side in (-1,1):
                    verts.append((center[0]-dy*side*width, center[1]+dx*side*width, center[2]))
                    heights.append(h*t*t)
            faces.extend(tuple(idx+i for i in (j,j+1,j+3,j+2)) for j in (0,2,4))
            shades.extend([rng.randrange(len(grass_mats))]*3)
    grass = mesh_object(f"Meadow ripple strip {band+1}", verts, faces, grass_mats)
    for poly, shade in zip(grass.data.polygons, shades):
        poly.material_index = shade
    grass.shape_key_add(name="Rest")
    bend = grass.shape_key_add(name="Wind bend")
    for pt, (x,y,z), h in zip(bend.data, verts, heights):
        pt.co = (x+.56*h, y+.23*h, z-.15*h)
    arrival = min(11, band*.83)
    for f,v in [(1,.02),(12+arrival,.05),(19+arrival,.94),(25+arrival,.25),
                (29+arrival,.49),(36+arrival,.04),(48,.025)]:
        bend.value = v
        bend.keyframe_insert("value", frame=f)

leaf_colors = [(.48,.145,.024),(.67,.28,.039),(.55,.365,.073),(.31,.082,.025)]
leaf_mats = [material("Autumn leaf %d" % i,c,.66)[0] for i,c in enumerate(leaf_colors)]
vein = material("Leaf vein", (.38,.22,.059))[0]

def falling_leaf(index, points, length, color):
    verts, faces = [], []
    for j in range(15):
        t = j/14
        width = length*.245 * sin(pi*t)**.7 * (1+.19*sin(j*2.6))
        for s in (-1,-.035,.035,1):
            verts.append((width*s, length*(t-.5), .21*width*abs(s)+.15*length*(t-.36)**2))
    for j in range(14):
        for k in range(3):
            i = 4*j+k
            faces.append((i,i+1,i+5,i+4))
    leaf = mesh_object(f"Falling leaf {index}", verts, faces, [leaf_mats[color],vein])
    for p in leaf.data.polygons:
        p.material_index = int(p.index % 3 == 1)
        p.use_smooth = True
    # Place paths relative to the locked camera so the leaves clear the face.
    basis = cam.rotation_euler.to_matrix()
    for j, (frame, x,y,depth) in enumerate(points):
        leaf.location = cam.location + basis @ Vector((x,y,-depth))
        leaf.rotation_euler = (0.62+j*.72, .24+j*.67, -.82+j*.78+index*.6)
        leaf.keyframe_insert("location",frame=frame)
        leaf.keyframe_insert("rotation_euler",frame=frame)

falling_leaf(1, [(11,.11,.255,1.29),(16,.10,.149,1.27),(22,.135,.090,1.25),
                 (28,.164,.024,1.24),(36,.154,-.058,1.25),(43,.20,-.133,1.29),
                 (49,.191,-.242,1.32)], .058, 1)
falling_leaf(2, [(14,.37,.38,2.1),(23,.312,.16,2.07),(32,.37,-.028,2.1),
                 (49,.405,-.238,2.19)], .079, 2)
falling_leaf(3, [(21,.22,.33,1.50),(30,.243,.169,1.55),(40,.214,.008,1.58),
                 (52,.29,-.177,1.67)], .045, 0)
falling_leaf(4, [(13,.47,.65,3.35),(26,.50,.21,3.24),(38,.57,-.16,3.1),
                 (48,.53,-.41,3.08)], .086, 1)
falling_leaf(5, [(28,.315,.40,1.66),(37,.335,.116,1.66),(48,.29,-.174,1.65)], .038, 3)

world = bpy.data.worlds.new("Late afternoon meadow")
scene.world = world
world.use_nodes = True
nodes = world.node_tree.nodes
env = nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(str(ENV / "autumn_meadow_1k.hdr"))
bg = nodes.get("Background")
world.node_tree.links.new(env.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = .52

def light(name, kind, position, target, energy, color, size):
    data = bpy.data.lights.new(name, kind)
    data.energy, data.color = energy, color
    if kind == "AREA":
        data.shape, data.size = "DISK", size
    else:
        data.angle = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    aim(obj,target)

light("Low sun across the field", "SUN", (3.1,4.4,3.5), (0,0,.8), 2.3, (1,.79,.54), .10)
light("Open sky through the branches", "AREA", (1.15,-.72,2.35), (0,-.08,1.04),
      46, (.74,.84,1), 1.9)
light("Meadow bounce", "AREA", (-.69,-1.02,1.04), (0,-.13,1.1), 17, (1,.87,.68), 1.25)

scene.frame_start = 1
scene.frame_end = 48
scene.render.fps = 12
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "AgX"
scene.timeline_markers.new("Watching", frame=1)
scene.timeline_markers.new("Breeze and falling leaf", frame=13)
scene.timeline_markers.new("Release", frame=33)
scene.frame_set(1)
