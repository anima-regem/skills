"""Build Under the Tree from Blender factory startup."""
from pathlib import Path
import math
import random

import bpy
from mathutils import Vector
from mathutils.noise import noise_vector

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ENV = ASSETS / "environment"
rng = random.Random(35)
sin, cos, tau = math.sin, math.cos, math.tau

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 32
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return mat, shader


def image(name, color_space=None):
    img = bpy.data.images.load(str(ENV / name))
    if color_space:
        img.colorspace_settings.name = color_space
    img.filepath = "//assets/environment/" + name
    img.pack()
    return img


def mesh(name, verts, faces, materials):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    for mat in materials:
        data.materials.append(mat)
    return obj


def animate(obj, prop, keys):
    for frame, value in keys:
        setattr(obj, prop, value)
        obj.keyframe_insert(data_path=prop, frame=frame)


with bpy.data.libraries.load(str(ASSETS / "einar.blend"), link=False) as (_, target):
    target.collections = ["CH-einar"]
scene.collection.children.link(target.collections[0])
target.collections[0].name = "Silas • field watcher"
rig = bpy.data.objects["RIG-einar"]
rig.animation_data_clear()
for obj in target.collections[0].all_objects:
    if obj.name.endswith(".messy") or obj.name == "GEO-einar_hat":
        obj.hide_render = True
    if obj.name.startswith("WGT-"):
        obj.hide_render = True


def recolor(name, color, amount):
    mat = bpy.data.materials.get(name)
    if not mat or not mat.use_nodes:
        return
    tree = mat.node_tree
    for shader in list(tree.nodes):
        if shader.type != "BSDF_PRINCIPLED":
            continue
        socket = shader.inputs["Base Color"]
        if socket.is_linked:
            original = socket.links[0].from_socket
            tint = tree.nodes.new("ShaderNodeMixRGB")
            tint.blend_type = "MULTIPLY"
            tint.inputs[0].default_value = amount
            tint.inputs[2].default_value = (*color, 1)
            tree.links.new(original, tint.inputs[1])
            tree.links.new(tint.outputs[0], socket)
        else:
            socket.default_value = (*color, 1)


recolor("einar.jacket.canvas", (0.27, 0.52, 0.66), 0.87)
recolor("einar.jacket.collar", (0.27, 0.52, 0.66), 0.87)
recolor("einar.sweater", (0.36, 0.43, 0.43), 0.65)
recolor("eyes.iris", (0.28, 0.36, 0.21), 0.44)
recolor("einar.hair", (0.36, 0.48, 0.60), 0.72)

bones = rig.pose.bones
animate(bones["FK-Head"], "rotation_euler", [
    (1, (0.012, 0.020, -0.024)), (15, (0.012, 0.020, -0.024)),
    (19, (0.011, 0.025, -0.024)), (26, (0.028, 0.093, -0.012)),
    (32, (0.065, 0.117, -0.008)), (48, (0.071, 0.108, -0.009)),
])
animate(bones["MSTR-TGT-Eyes"], "location", [
    (1, (-0.086, 0, 0.009)), (13, (-0.086, 0, 0.009)),
    (16, (-0.245, 0, 0.055)), (21, (-0.277, 0, 0.020)),
    (26, (-0.257, 0, -0.055)), (32, (-0.222, 0, -0.126)),
    (38, (-0.178, 0, -0.120)), (48, (-0.173, 0, -0.115)),
])
animate(bones["FK-Chest"], "rotation_euler", [
    (1, (-0.004, 0, 0)), (12, (-0.010, 0, 0)), (28, (-0.002, 0, 0)),
    (41, (-0.008, 0, 0)), (48, (-0.005, 0, 0)),
])
for side, sign in (("L", 1), ("R", -1)):
    animate(bones["Blink." + side], "location", [
        (1, (0, 0, 0)), (33, (0, 0, 0)), (34, (0, -0.003, 0)),
        (35, (0, -0.006, 0)), (36.2, (0, -0.0018, 0)), (38, (0, 0, 0)),
    ])
    animate(bones["ACT-Eyebrow_Inner." + side], "location", [
        (1, (-0.0022 * sign, -0.0024, 0)), (13, (-0.0022 * sign, -0.0024, 0)),
        (18, (-0.0014 * sign, -0.0003, 0)), (31, (-0.0016 * sign, -0.0012, 0)),
        (41, (-0.0008 * sign, -0.0008, 0)), (48, (-0.0008 * sign, -0.0008, 0)),
    ])
    animate(bones["ACT-Mouth_Corner." + side], "location", [
        (1, (-0.0017 * sign, -0.0011, 0)), (32, (-0.0017 * sign, -0.0011, 0)),
        (41, (-0.0002 * sign, -0.0002, 0)), (48, (-0.0002 * sign, -0.0002, 0)),
    ])

# Eye-level, locked three-quarter close-up.
camera_data = bpy.data.cameras.new("Portrait lens")
camera = bpy.data.objects.new("Locked close-up", camera_data)
scene.collection.objects.link(camera)
camera.location = (0.355, -1.007, 1.688)
point_at(camera, (0.058, -0.100, 1.651))
camera_data.lens = 62
camera_data.dof.use_dof = True
camera_data.dof.focus_distance = (camera.location - Vector((0.013, -0.122, 1.673))).length
camera_data.dof.aperture_fstop = 5.0
camera_data.dof.aperture_blades = 8
scene.camera = camera

world = bpy.data.worlds.new("Meadow sky")
scene.world = world
world.use_nodes = True
tree = world.node_tree
environment = tree.nodes.new("ShaderNodeTexEnvironment")
environment.image = image("autumn_meadow_1k.hdr")
tree.links.new(environment.outputs["Color"], tree.nodes["Background"].inputs["Color"])
tree.nodes["Background"].inputs["Strength"].default_value = 0.41


def light(name, kind, location, target, color, power, size):
    data = bpy.data.lights.new(name, kind)
    data.color = color
    data.energy = power
    if kind == "SUN":
        data.angle = size
    else:
        data.shape = "DISK"
        data.size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    point_at(obj, target)
    return obj


light("Late sun", "SUN", (-5, 6, 6), (0, 0, 2), (1, 0.73, 0.47), 2.1, 0.16)
light("Open sky through canopy", "AREA", (0.00, -1.65, 2.75), (0, 0, 1.61),
      (0.76, 0.86, 1), 56, 1.7)
light("Warm field bounce", "AREA", (1.25, -0.20, 1.2), (0, 0, 1.61),
      (1, 0.85, 0.62), 20, 1.25)
light("Sun through leaves", "AREA", (0.54, 0.73, 2.27), (0, 0, 1.69),
      (1, 0.70, 0.39), 45, 0.85)

bark, bark_shader = material("Oak • furrowed bark", (0.16, 0.095, 0.051))
nodes = bark.node_tree.nodes
links = bark.node_tree.links
uv = nodes.new("ShaderNodeTexCoord")
for filename in ("oak_bark_diffuse.jpg", "oak_bark_normal.jpg"):
    normal = "normal" in filename
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image(filename, "Non-Color" if normal else None)
    links.new(uv.outputs["UV"], tex.inputs["Vector"])
    if normal:
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.inputs["Strength"].default_value = 0.85
        links.new(tex.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], bark_shader.inputs["Normal"])
    else:
        links.new(tex.outputs["Color"], bark_shader.inputs["Base Color"])

# Irregular trunk with continuous cylindrical UVs.
verts, faces = [], []
sides, rings = 104, 58
for row in range(rings):
    z = 0.61 + 3.7 * row / (rings - 1)
    for col in range(sides):
        a = tau * col / sides
        n = noise_vector((cos(a) * 3.2, sin(a) * 3.2, z * 2.1)).x
        radius = 0.35 - 0.034 * (z - 1.5) + 0.020 * sin(9 * a + z) + 0.019 * n
        radius += 0.10 * math.exp(-(z - 0.61) * 6) * (0.7 + 0.3 * cos(6 * a))
        verts.append((-0.193 + radius * cos(a) - 0.065 * (z - 1.4),
                      0.338 + radius * sin(a) + 0.025 * sin(3 * z), z))
for row in range(rings - 1):
    for col in range(sides):
        a, b = row * sides + col, row * sides + (col + 1) % sides
        faces.append((a, b, b + sides, a + sides))
oak = mesh("Old oak", verts, faces, [bark])
uv_layer = oak.data.uv_layers.new()
for poly in oak.data.polygons:
    row, col = divmod(poly.index, sides)
    poly.use_smooth = True
    for loop, (u, v) in zip(poly.loop_indices, ((col, row), (col + 1, row),
                                                (col + 1, row + 1), (col, row + 1))):
        uv_layer.data[loop].uv = (u / sides * 3.7, v / (rings - 1) * 6.6)

soil, ground_shader = material("Field • moss and dry ground", (0.22, 0.23, 0.075))
nodes = soil.node_tree.nodes
links = soil.node_tree.links
noise = nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 28
ramp = nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.19
ramp.color_ramp.elements[0].color = (0.093, 0.083, 0.032, 1)
ramp.color_ramp.elements[1].position = 0.83
ramp.color_ramp.elements[1].color = (0.32, 0.33, 0.125, 1)
links.new(noise.outputs["Fac"], ramp.inputs[0])
links.new(ramp.outputs[0], ground_shader.inputs["Base Color"])


def height(x, y):
    return 0.69 + 0.095 * sin(y * 0.57) + 0.085 * sin(x * 0.62 + y * 0.28)


verts = [(x, y, height(x, y)) for y in range(-9, 36) for x in range(-16, 29)]
faces = [(i, i + 1, i + 46, i + 45) for i in range(len(verts) - 45) if (i + 1) % 45]
ground = mesh("Rolling meadow", verts, faces, [soil])
for polygon in ground.data.polygons:
    polygon.use_smooth = True

grass_materials = []
for name, color in [
    ("Olive", (0.20, 0.27, 0.055)), ("Sage", (0.29, 0.35, 0.105)),
    ("Wheat", (0.47, 0.36, 0.12)), ("Moss", (0.115, 0.19, 0.041)),
    ("Seed heads", (0.48, 0.38, 0.17)),
]:
    mat, shader = material(name, color)
    shader.inputs["Subsurface Weight"].default_value = 0.09
    grass_materials.append(mat)


def meadow_patch(index, count, xbounds, ybounds, animated):
    verts, faces, colors, wind = [], [], [], []
    for _ in range(count):
        x, y = rng.uniform(*xbounds), rng.uniform(*ybounds)
        if (x + 0.13) ** 2 + (y - 0.15) ** 2 < 0.42:
            continue
        z = height(x, y)
        tall = rng.random() < 0.12
        for blade in range(3 if tall else 5):
            a = rng.uniform(0, tau)
            ux, uy = cos(a), sin(a)
            h = rng.uniform(0.31, 0.69) if tall else rng.uniform(0.075, 0.37)
            width = rng.uniform(0.003, 0.014) * (0.53 if tall else 1)
            bend = rng.uniform(0.10, 0.68) * h
            offset = rng.uniform(0.0, 0.09)
            bx, by = x + ux * offset, y + uy * offset
            start = len(verts)
            for t, taper in ((0, 0.40), (0.40, 1), (0.75, 0.55), (1, 0.025)):
                for side in (-1, 1):
                    verts.append((bx + ux * bend * t * t - uy * width * taper * side,
                                  by + uy * bend * t * t + ux * width * taper * side,
                                  z + h * t))
                    wind.append((x, y, h * t * t))
            tint = rng.randrange(4)
            for k in (0, 2, 4):
                faces.append(tuple(start + k + j for j in (0, 1, 3, 2)))
                colors.append(tint)
            if tall:
                px, py, pz = verts[-1]
                start = len(verts)
                verts.extend([(px - 0.012, py, pz - 0.028), (px, py - 0.012, pz - 0.025),
                              (px + 0.012, py, pz - 0.028), (px, py + 0.012, pz - 0.025),
                              (px + ux * 0.025, py + uy * 0.025, pz + 0.049)])
                wind.extend([(x, y, h)] * 5)
                for k in range(4):
                    faces.append((start + k, start + (k + 1) % 4, start + 4))
                    colors.append(4)
    obj = mesh(f"Meadow plants {index}", verts, faces, grass_materials)
    for polygon, color in zip(obj.data.polygons, colors):
        polygon.material_index = color
    if animated:
        # A traveling ripple bends rooted blades, with progressively stronger tip displacement.
        obj.shape_key_add(name="Still")
        for frame in range(10, 47, 3):
            key = obj.shape_key_add(name=f"Wind at {frame}")
            time = (frame - 1) / 12
            envelope = max(0, sin(math.pi * max(0, min(1, (time - 0.80) / 2.98)))) ** 1.65
            coords = []
            for (vx, vy, vz), (x, y, strength) in zip(verts, wind):
                gust = envelope * strength * (0.17 + 0.22 * sin(6.7 * time - 2.1 * x - y * 1.3))
                coords.extend((vx + gust, vy + gust * 0.45, vz - abs(gust) * 0.20))
            key.data.foreach_set("co", coords)
            animate(key, "value", [(frame - 3, 0), (frame, 1), (frame + 3, 0)])


meadow_patch(1, 1050, (-2.3, 5.4), (0.4, 8.0), True)
meadow_patch(2, 4900, (-12, 19), (7.9, 26), False)

leaf_materials = []
for name, color in [
    ("Honey", (0.57, 0.255, 0.045)), ("Copper", (0.42, 0.122, 0.032)),
    ("Bronze", (0.44, 0.31, 0.067)), ("Vein", (0.25, 0.13, 0.039)),
]:
    mat, shader = material(name, color, 0.51)
    shader.inputs["Subsurface Weight"].default_value = 0.16
    leaf_materials.append(mat)


def oak_leaf(name, length, tint):
    outline = [(0, -0.53), (-0.13, -0.38), (-0.31, -0.26), (-0.25, -0.15),
               (-0.40, -0.05), (-0.28, 0.05), (-0.36, 0.16), (-0.21, 0.25),
               (-0.23, 0.33), (0, 0.51), (0.20, 0.36), (0.19, 0.27),
               (0.35, 0.16), (0.25, 0.07), (0.38, -0.03), (0.24, -0.16),
               (0.28, -0.24), (0.12, -0.37)]
    verts = [(0, 0, 0.040 * length)]
    verts.extend((x * length, y * length, length * (0.24 * y * y + 0.16 * x * sin(11 * y)))
                 for x, y in outline)
    faces = [(0, (i + 1) % len(outline) + 1, i + 1) for i in range(len(outline))]
    stem = len(verts)
    verts.extend((x * length, y * length, z * length) for x, y, z in
                 [(-0.014, -0.69, 0.06), (0.014, -0.69, 0.06),
                  (0.008, -0.08, 0.046), (-0.008, -0.08, 0.046)])
    faces.append((stem, stem + 1, stem + 2, stem + 3))
    obj = mesh(name, verts, faces, [leaf_materials[tint], leaf_materials[3]])
    obj.data.polygons[-1].material_index = 1
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


# The featured leaf occupies the right-hand gutter throughout its pass.
right = camera.rotation_euler.to_matrix().col[0].copy()
up = camera.rotation_euler.to_matrix().col[1].copy()
forward = -camera.rotation_euler.to_matrix().col[2].copy()
featured = oak_leaf("Leaf he follows", 0.046, 0)
for frame in range(1, 49):
    t = (frame - 14) / 12
    depth = 0.995 + 0.062 * t
    sx = 0.158 + 0.026 * t + 0.015 * sin(t * 4.8)
    sy = 0.102 - 0.112 * t + 0.010 * sin(t * 6) + 0.68 * min(t, 0) ** 2
    featured.location = camera.location + depth * forward + sx * right + sy * up
    featured.rotation_euler = (0.55 + t * 2.8, 0.67 * sin(5 * t), -0.7 + 1.0 * sin(3.3 * t))
    featured.keyframe_insert(data_path="location", frame=frame)
    featured.keyframe_insert(data_path="rotation_euler", frame=frame)

for i in range(9):
    leaf = oak_leaf(f"Falling oak leaf {i + 1}", rng.uniform(0.041, 0.079), i % 3)
    start = rng.uniform(0.85, 2.85)
    depth = rng.uniform(1.24, 2.95)
    side = rng.uniform(0.30, 0.44)
    speed = rng.uniform(0.13, 0.35)
    phase = rng.uniform(0, tau)
    for frame in range(1, 49):
        t = (frame - 1) / 12 - start
        sx = depth * (side * 0.55 + 0.021 * t) + 0.042 * sin(t * 3.5 + phase)
        sy = depth * 0.18 - speed * t
        leaf.location = camera.location + depth * forward + sx * right + sy * up
        leaf.rotation_euler = (phase + 3.4 * t, sin(4 * t + phase), phase + 1.5 * t)
        leaf.keyframe_insert(data_path="location", frame=frame)
        leaf.keyframe_insert(data_path="rotation_euler", frame=frame)

scene.timeline_markers.new("Watch", frame=1)
scene.timeline_markers.new("Breeze", frame=13)
scene.timeline_markers.new("Settle", frame=32)
scene["Credits"] = ("Einar rig base by Blender Foundation, CC BY 4.0. "
                    "Oak bark and Autumn Meadow by Poly Haven contributors, CC0.")
scene.frame_set(1)
