"""Under the Tree. Build with Blender 5.2 using --background --python scene.py."""
from math import cos, exp, pi, sin
from pathlib import Path
from random import Random

import bpy
from mathutils import Vector

ASSETS = Path(__file__).resolve().parent / "assets"
rng = Random(716)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = "AgX"


def material(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat, bsdf


def mesh(name, vertices, faces, materials):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    for mat in materials:
        data.materials.append(mat)
    return obj


def animate(obj, attr, keys):
    for frame, value in keys:
        setattr(obj, attr, value)
        obj.keyframe_insert(data_path=attr, frame=frame)


# Einar Rig (CC BY 4.0), Blender Foundation / studio.blender.org.
# The supplied production rig is the base for this character's costume and performance.
with bpy.data.libraries.load(str(ASSETS / "einar.blend"), link=False) as (_, target):
    target.collections = ["CH-einar"]
cast = target.collections[0]
scene.collection.children.link(cast)
rig = bpy.data.objects["RIG-einar"]
for obj in cast.all_objects:
    if obj.name.startswith("WGT-"):
        obj.hide_render = True
    if obj.parent is None:
        obj.location.z -= .54

# A muted blue field coat and charcoal wool cap.
for label, color, names in [
    ("Petrol canvas", (.031, .082, .087), ["jacket_main", "jacket_collar1", "jacket_collar2"]),
    ("Charcoal wool", (.049, .043, .033), ["hat"]),
]:
    mat, bsdf = material(label, color, .83)
    tree = mat.node_tree
    noise = tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 310
    bump = tree.nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = .0012
    bump.inputs["Strength"].default_value = .32
    tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    for name in names:
        obj = bpy.data.objects["GEO-einar_" + name]
        for index in range(len(obj.data.materials)):
            obj.data.materials[index] = mat

# Adjust the nose bridge and tip on the existing skin without disturbing the eyelids.
skin = bpy.data.objects["GEO-einar_head"]
if skin.data.shape_keys is None:
    skin.shape_key_add(name="Rig base")
portrait = skin.shape_key_add(name="Field scout likeness")
for point in portrait.data:
    x, y, z = point.co
    bridge = exp(-((x-.001)/.022)**2 - ((z-1.647)/.024)**2)
    front = min(1, max(0, (-y-.109)/.036))
    point.co.x += (.16*x + .0028) * bridge * front
    point.co.y -= .006 * bridge * front
portrait.value = 1

# Use the packed clean skin maps for a lightweight Eevee surface.
skin_mat, bsdf = material("Scout skin", (.38, .19, .13), .51)
bsdf.inputs["Subsurface Weight"].default_value = .105
bsdf.inputs["Subsurface Radius"].default_value = (1, .5, .31)
bsdf.inputs["Subsurface Scale"].default_value = .013
skin_tree = skin_mat.node_tree
detail = skin_tree.nodes.new("ShaderNodeBump")
detail.inputs["Strength"].default_value = .27
detail.inputs["Distance"].default_value = .0016
skin_tree.links.new(detail.outputs["Normal"], bsdf.inputs["Normal"])
for node_name, socket in [("Image Texture.005", bsdf.inputs["Base Color"]),
                          ("Image Texture.007", bsdf.inputs["Roughness"]),
                          ("Image Texture.002", detail.inputs["Height"])]:
    original = skin.data.materials[0].node_tree.nodes[node_name]
    tex = skin_tree.nodes.new("ShaderNodeTexImage")
    tex.image = original.image
    for link in original.inputs["Vector"].links:
        if link.from_node.type == "UVMAP":
            uv_map = skin_tree.nodes.new("ShaderNodeUVMap")
            uv_map.uv_map = link.from_node.uv_map
            skin_tree.links.new(uv_map.outputs["UV"], tex.inputs["Vector"])
    skin_tree.links.new(tex.outputs["Color"], socket)
skin.data.materials[0] = skin_mat

groom, bsdf = material("Ash brown strands", (.048, .026, .015), .73)
tree = groom.node_tree
strand = tree.nodes.new("ShaderNodeHairInfo")
tint = tree.nodes.new("ShaderNodeValToRGB")
tint.color_ramp.elements[0].color = (.024, .013, .008, 1)
tint.color_ramp.elements[1].color = (.205, .147, .095, 1)
tint.color_ramp.elements.new(.82).color = (.061, .034, .021, 1)
tree.links.new(strand.outputs["Random"], tint.inputs["Fac"])
tree.links.new(tint.outputs["Color"], bsdf.inputs["Base Color"])
for obj in cast.all_objects:
    if obj.type == "CURVES" and obj.data.materials[0].name == "einar.hair":
        obj.data.materials[0] = groom

bones = rig.pose.bones
head = bones["FK-Head"]
head.rotation_mode = "XYZ"
animate(head, "rotation_euler", [
    (1, (.012, .08, -.012)), (18, (.012, .08, -.012)),
    (28, (.017, .128, -.007)), (35, (.006, .135, -.008)), (48, (.003, .127, -.01)),
])
animate(bones["MSTR-TGT-Eyes"], "location", [
    (1, (-.075, 0, .006)), (14, (-.075, 0, .006)),
    (17, (-.201, 0, .012)), (25, (-.244, 0, -.060)),
    (32, (-.232, 0, -.125)), (39, (-.183, 0, -.104)), (48, (-.181, 0, -.098)),
])
for side in "LR":
    animate(bones["Blink." + side], "location", [
        (1, (0, -.0006, 0)), (35, (0, -.0006, 0)), (37, (0, -.006, 0)),
        (39, (0, .0006, 0)), (42, (0, 0, 0)), (48, (0, 0, 0)),
    ])
    animate(bones["ACT-Eyebrow_Inner." + side], "location", [
        (1, (0, -.0017, 0)), (15, (0, -.0017, 0)),
        (25, (0, -.0008, 0)), (48, (0, -.0005, 0)),
    ])
    animate(bones["ACT-Mouth_Corner." + side], "location", [
        (1, (0, -.0013, 0)), (33, (0, -.0013, 0)), (42, (0, 0, 0)), (48, (0, 0, 0)),
    ])
chest = bones["MSTR-Spine_Chest"]
chest.rotation_mode = "XYZ"
animate(chest, "rotation_euler", [(1, (0, 0, 0)), (12, (.003, 0, 0)),
                                  (25, (0, 0, 0)), (38, (.003, 0, 0)), (48, (0, 0, 0))])

aim = Vector((.030, -.08, 1.102))
cam_offset = Vector((.46, -.888, .012)).normalized()
right = Vector((-cam_offset.y, cam_offset.x, 0))
back = Vector((-cam_offset.x, -cam_offset.y, 0))


def stage(x, depth, z):
    return Vector((aim.x, aim.y, z)) + x * right + depth * back


def point(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


cam = bpy.data.objects.new("Portrait camera", bpy.data.cameras.new("Portrait camera"))
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = aim + cam_offset * 1.12
point(cam, aim)
cam.data.lens = 76
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = 1.105
cam.data.dof.aperture_fstop = 5.0

bark, bark_bsdf = material("Oak bark", (.12, .076, .04), .91)
nodes, links = bark.node_tree.nodes, bark.node_tree.links
for suffix in ("diffuse", "normal"):
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(ASSETS / "environment" / f"oak_bark_{suffix}.jpg"))
    tex.image.pack()
    if suffix == "diffuse":
        links.new(tex.outputs["Color"], bark_bsdf.inputs["Base Color"])
    else:
        tex.image.colorspace_settings.name = "Non-Color"
        normal = nodes.new("ShaderNodeNormalMap")
        normal.inputs["Strength"].default_value = .85
        links.new(tex.outputs["Color"], normal.inputs["Color"])
        links.new(normal.outputs["Normal"], bark_bsdf.inputs["Normal"])

vertices, faces = [], []
sides = 72
rings = 33
for j in range(rings):
    z = -.12 + 3.2 * j / (rings - 1)
    center = stage(-.295 - .026 * sin(z * 1.6), .254 + .035 * sin(z * 2), z)
    for i in range(sides):
        a = i * 2 * pi / sides
        radius = (.255 - .029 * z + .13 * exp(-z * 6)
                  + .016 * sin(7*a + z*1.2) + .008 * sin(19*a - z*.9)
                  + .011 * sin(3*a + z*4))
        vertices.append(center + Vector((radius*cos(a), radius*sin(a), 0)))
        if j:
            k = (i + 1) % sides
            faces.append(((j-1)*sides+i, (j-1)*sides+k, j*sides+k, j*sides+i))
trunk = mesh("Oak at the field edge", vertices, faces, [bark])
uv = trunk.data.uv_layers.new()
for face in trunk.data.polygons:
    face.use_smooth = True
    for n, loop in enumerate(face.loop_indices):
        row, col = divmod(trunk.data.loops[loop].vertex_index, sides)
        i = face.index % sides + int(n in (1, 2))
        uv.data[loop].uv = (1.8 * i / sides, row * .106)

world = bpy.data.worlds.new("Afternoon sky")
scene.world = world
world.use_nodes = True
world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.32, .43, .56, 1)
world.node_tree.nodes.get("Background").inputs["Strength"].default_value = .55


def light(name, kind, location, target, energy, color, size):
    data = bpy.data.lights.new(name, kind)
    data.energy, data.color = energy, color
    if kind == "AREA":
        data.shape, data.size = "DISK", size
    else:
        data.angle = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    point(obj, target)


light("Low sun across the field", "SUN", (4, 5, 4), (0, 0, 0), 2.35, (1, .76, .52), .095)
light("Open sky under the oak", "AREA", (.7, -1.35, 2.1), aim, 49, (.68, .80, 1), 1.5)
light("Warm bounce from dry grass", "AREA", (-.26, -.85, .56), aim, 13, (1, .70, .46), .85)

earth, shader = material("Field floor", (.10, .12, .036), .97)
nodes, links = earth.node_tree.nodes, earth.node_tree.links
noise = nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 22
ramp = nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (.048, .061, .018, 1)
ramp.color_ramp.elements[1].color = (.24, .235, .076, 1)
links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
links.new(ramp.outputs["Color"], shader.inputs["Base Color"])


def ground(x, y):
    return 1.01 * (1 - exp(-max(0, y-.65)*.30)) + .075*sin(.72*x+.37*y)


vertices = [stage(x, y, ground(x, y)) for y in range(-3, 34) for x in range(-25, 26)]
faces = [(i, i+1, i+52, i+51) for i in range(len(vertices)-51) if i%51 != 50]
mesh("Rising meadow", vertices, faces, [earth])

grass = []
for hue in [(.081, .132, .031), (.167, .206, .055), (.24, .235, .073),
            (.29, .231, .093), (.35, .29, .12)]:
    mat, shader = material("Meadow blade", hue, .69)
    shader.inputs["Subsurface Weight"].default_value = .07
    grass.append(mat)

# Shared moving patch meshes keep the wave spatially coherent in Eevee.
for patch in range(207):
    y = rng.uniform(1.1, 5.5) if patch < 92 else rng.uniform(5.5, 22)
    x = rng.uniform(-.24, .27) * (1.12+y)
    vertices, faces, colors = [], [], []
    for blade in range(65 if patch < 92 else 120):
        dx, dy = rng.uniform(-.46, .46), rng.uniform(-.48, .48)
        h = rng.uniform(.22, .76) if y < 5.5 else rng.uniform(.16, .56)
        w = rng.uniform(.005, .017)
        a = rng.uniform(0, 2*pi)
        lean = rng.uniform(.12, .6) * h
        z = ground(x+dx, y+dy) - ground(x, y)
        start = len(vertices)
        for t, width in [(0, .56), (.40, 1), (.74, .70), (1, .025)]:
            for sign in (-1, 1):
                px = dx + t*t*lean*cos(a) - sign*w*width*sin(a)
                py = dy + t*t*lean*sin(a) + sign*w*width*cos(a)
                vertices.append((px, py, z + t*h))
        faces.extend((start+i, start+i+1, start+i+3, start+i+2) for i in (0, 2, 4))
        colors.extend([rng.randrange(len(grass))]*3)
    obj = mesh("Meadow patch", vertices, faces, grass)
    obj.location = stage(x, y, ground(x, y))
    obj.rotation_euler.z = right.to_track_quat("X", "Z").to_euler().z
    for polygon, color in zip(obj.data.polygons, colors):
        polygon.material_index = color
    root = obj.shape_key_add(name="Still")
    bent = obj.shape_key_add(name="Bend with gust")
    for i, (src, dst) in enumerate(zip(root.data, bent.data)):
        t = (i % 8)//2
        dst.co.x = src.co.x + (.0, .032, .105, .21)[t]
        dst.co.z = src.co.z - (.0, .006, .025, .075)[t]
    delay = round(min(8, max(0, (x+.4)*3 + y*.32)))
    animate(bent, "value", [(1, 0), (11+delay, 0), (17+delay, .95),
                           (22+delay, .32), (26+delay, .6), (33+delay, .09), (46, 0)])

leaf_mats = []
for name, hue in [("Amber", (.52, .22, .041)), ("Copper", (.35, .085, .024)),
                  ("Ochre", (.39, .31, .065)), ("Vein", (.22, .117, .032))]:
    mat, shader = material(name, hue, .54)
    shader.inputs["Subsurface Weight"].default_value = .16
    leaf_mats.append(mat)

outline = [(-.51, 0), (-.40, -.17), (-.19, -.28), (-.02, -.23),
           (.15, -.29), (.31, -.19), (.49, 0), (.29, .15), (.14, .24),
           (-.04, .20), (-.21, .27), (-.41, .15)]
for index, (start, depth, x, speed, length) in enumerate([
    (13, .30, .246, .0066, .045), (9, .89, .335, .0099, .041),
    (18, 1.24, .50, .012, .057), (24, .55, .327, .0067, .027),
    (29, 1.88, .62, .0092, .064), (15, 2.1, .45, .0086, .041),
]):
    verts = [(0, 0, .10)] + [(u, v, -.16*abs(v)+.11*u*u) for u, v in outline]
    leaf_faces = [(0, j+1, 1+((j+1) % len(outline))) for j in range(len(outline))]
    verts += [(-.63, -.014, .005), (-.63, .014, .005), (.39, .009, .062), (.39, -.009, .062)]
    leaf_faces.append(tuple(range(len(verts)-4, len(verts))))
    leaf = mesh("Tracked amber leaf" if index == 0 else "Falling oak leaf",
                verts, leaf_faces, [leaf_mats[index%3], leaf_mats[3]])
    leaf.data.polygons[-1].material_index = 1
    leaf.scale = (length,)*3
    motion, spin = [], []
    for frame in (*range(1, 49, 2), 48):
        age = frame - start
        z = 1.287 + .047*depth - age*speed + .014*sin(age*.30+index)
        drift = .037*sin(age*.24+index) - .0029*max(0, age)
        motion.append((frame, stage(x+drift, depth+.03*sin(age*.29), z)))
        spin.append((frame, (1.13 + .64*sin(age*.37+index), age*.15, .48*sin(age*.27))))
    animate(leaf, "location", motion)
    animate(leaf, "rotation_euler", spin)

scene.frame_set(1)
assert scene.camera == cam and scene.frame_end == 48 and rig.animation_data.action
