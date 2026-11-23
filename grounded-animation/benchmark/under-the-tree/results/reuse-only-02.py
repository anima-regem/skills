"""Under the Tree. Run with Blender in background mode using --python scene.py.

Einar Rig (CC BY 4.0) Blender Foundation | studio.blender.org
https://studio.blender.org/characters/einar/v1/
Adapted posing, wardrobe, shading and shot staging for this scene.
Poly Haven (CC0): Jolcham Oak Bark by Charlotte Baglioni, Grass Medium 01
by Rob Tuytel and Rico Cilliers, Autumn Meadow by Sergej Majboroda.
https://polyhaven.com/a/jolcham_oak_bark_01
https://polyhaven.com/a/grass_medium_01
https://polyhaven.com/a/autumn_meadow
"""

from pathlib import Path
from math import cos, sin, pi, exp, radians
from random import Random

import bpy
from mathutils import Euler, Quaternion, Vector

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ENV = ASSETS / "environment"
rng = Random(26)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene["Credits"] = __doc__
scene.frame_start = 1
scene.frame_end = 48
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.view_settings.view_transform = "AgX"

with bpy.data.libraries.load(str(ASSETS / "einar.blend"), link=False) as (_, dst):
    dst.collections = ["CH-einar"]
scene.collection.children.link(dst.collections[0])
rig = bpy.data.objects["RIG-einar"]
if rig.animation_data:
    rig.animation_data.action = None
rig["Character"] = "Silas, orchard keeper"

# Reshape the nose in every sculpt so the feature stays consistent as expressions blend.
skin = bpy.data.objects["GEO-einar_head"]
bpy.context.view_layer.update()
nose_offsets = []
for vertex in skin.data.shape_keys.reference_key.data:
    x, y, z = skin.matrix_world @ vertex.co
    ridge = exp(-((x / .020)**2 + ((z - 1.649) / .030)**2
                  + ((y + .151) / .026)**2))
    tip = exp(-((x / .026)**2 + ((z - 1.631) / .017)**2
                + ((y + .155) / .021)**2))
    nose_offsets.append(Vector((x * .16 * tip + .0023 * ridge,
                                -.007 * ridge - .003 * tip, -.003 * tip)))
for sculpt in skin.data.shape_keys.key_blocks:
    for vertex, offset in zip(sculpt.data, nose_offsets):
        vertex.co += offset

def tint(name, color, amount):
    material = bpy.data.materials.get(name)
    if not material or not material.use_nodes:
        return
    tree = material.node_tree
    for shader in list(tree.nodes):
        if not shader.inputs.get("Base Color"):
            continue
        socket = shader.inputs["Base Color"]
        if socket.is_linked:
            old = socket.links[0].from_socket
            blend = tree.nodes.new("ShaderNodeMixRGB")
            blend.blend_type = "MIX"
            blend.inputs[0].default_value = amount
            blend.inputs[2].default_value = (*color, 1)
            tree.links.new(old, blend.inputs[1])
            tree.links.new(blend.outputs[0], socket)
        else:
            socket.default_value = (*color, 1)

tint("einar.hat", (.042, .075, .062), .67)
tint("einar.jacket.canvas", (.15, .075, .038), .42)
tint("einar.jacket.collar", (.14, .090, .048), .40)
tint("einar.sweater", (.10, .12, .092), .45)
tint("einar.hair", (.044, .023, .013), .34)
tint("einar.skin", (.27, .149, .104), .17)
tint("eyes.iris", (.085, .117, .067), .21)
for obj in dst.collections[0].all_objects:
    if obj.name.endswith(".messy"):
        obj.hide_render = True

def bone_keys(name, channel, samples):
    bone = rig.pose.bones[name]
    for frame, value in samples:
        setattr(bone, channel, value)
        bone.keyframe_insert(data_path=channel, frame=frame, group=name)

def head(pitch, yaw, roll):
    return tuple(map(radians, (pitch, yaw, roll)))

bone_keys("FK-Head", "rotation_euler", [
    (1, head(1.8, 2, -2.8)), (13, head(1.8, 2, -2.8)),
    (18, head(1.8, 2, -2.8)), (25, head(2.1, 6.5, -1.6)),
    (32, head(4.4, 6.0, -1.8)), (39, head(4.9, 5.1, -2.1)),
    (48, head(4.7, 5.1, -2.1)),
])
bone_keys("MSTR-TGT-Eyes", "location", [
    (1, (-.075, 0, .025)), (13, (-.075, 0, .025)),
    (16, (-.255, 0, .03)), (21, (-.28, 0, -.008)),
    (28, (-.23, 0, -.105)), (33, (-.24, 0, -.151)),
    (39, (-.15, 0, -.138)), (48, (-.15, 0, -.138)),
])
for side, press in [("L", .0035), ("R", .0045)]:
    bone_keys("Blink." + side, "location", [
        (1, (0, -.0005, 0)), (31, (0, -.0005, 0)),
        (34, (0, -.006, 0)), (35, (0, -.0045, 0)),
        (37, (0, 0, 0)), (48, (0, 0, 0)),
    ])
    bone_keys("ACT-Eyebrow_Inner." + side, "location", [
        (1, (0, -press, 0)), (23, (0, -press * .85, 0)),
        (34, (0, -press, 0)), (43, (0, -press * .43, 0)),
        (48, (0, -press * .43, 0)),
    ])
    bone_keys("ACT-Mouth_Corner." + side, "location", [
        (1, (0, -.0025, 0)), (32, (0, -.0025, 0)),
        (40, (0, -.0003, 0)), (48, (0, -.0003, 0)),
    ])
bone_keys("MSTR-Spine_Chest", "location", [
    (1, (0, 0, 0)), (12, (0, .0023, .0006)), (25, (0, 0, 0)),
    (37, (0, .0018, .0004)), (48, (0, .0002, 0)),
])

def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

camera_data = bpy.data.cameras.new("Portrait lens")
camera = bpy.data.objects.new("Locked three-quarter close-up", camera_data)
scene.collection.objects.link(camera)
camera.location = (.68, -1.86, 1.731)
aim(camera, (.019, -.055, 1.647))
camera_data.lens = 125
camera_data.dof.use_dof = True
focus = bpy.data.objects.new("Eye plane", None)
scene.collection.objects.link(focus)
focus.location = (.01, -.147, 1.653)
camera_data.dof.focus_object = focus
camera_data.dof.aperture_fstop = 7.1
scene.camera = camera

def material(name, color, roughness):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    shader = m.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return m, shader

def mesh(name, vertices, faces, mat=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    if mat:
        data.materials.append(mat)
    return obj

bark, shader = material("Jolcham oak", (.13, .078, .043), .86)
tree = bark.node_tree
for filename, non_color in [("oak_bark_diffuse.jpg", False), ("oak_bark_normal.jpg", True)]:
    texture = tree.nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(ENV / filename))
    if non_color:
        texture.image.colorspace_settings.name = "Non-Color"
        normal = tree.nodes.new("ShaderNodeNormalMap")
        normal.inputs["Strength"].default_value = .72
        tree.links.new(texture.outputs["Color"], normal.inputs["Color"])
        tree.links.new(normal.outputs["Normal"], shader.inputs["Normal"])
    else:
        tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])

sides, rings = 120, 51
verts, faces = [], []
for j in range(rings):
    z = .35 + j * .066
    for i in range(sides):
        a = i * 2 * pi / sides
        radius = (.45 - .023 * (z - 1.4) + .022 * sin(7*a + .5*z)
                  + .012 * sin(17*a - 1.4*z) + .005 * sin(49*a + 2*z))
        verts.append((-.684 + .028 * sin(z * 2) + radius*cos(a),
                      .435 + .027 * sin(z) + radius*sin(a), z))
        if j:
            k = (i + 1) % sides
            faces.append(((j-1)*sides+i, (j-1)*sides+k, j*sides+k, j*sides+i))
trunk = mesh("Oak trunk", verts, faces, bark)
uv = trunk.data.uv_layers.new()
for polygon in trunk.data.polygons:
    polygon.use_smooth = True
    i = polygon.index % sides
    j = polygon.index // sides
    coordinates = [(i, j), (i+1, j), (i+1, j+1), (i, j+1)]
    for index, (u, v) in zip(polygon.loop_indices, coordinates):
        uv.data[index].uv = (u / sides * 3.8, v * .066 * 1.37)

world = bpy.data.worlds.new("Autumn afternoon")
world.use_nodes = True
scene.world = world
tree = world.node_tree
env = tree.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(str(ENV / "autumn_meadow_1k.hdr"))
coordinates = tree.nodes.new("ShaderNodeTexCoord")
mapping = tree.nodes.new("ShaderNodeMapping")
mapping.inputs["Rotation"].default_value.z = radians(104)
tree.links.new(coordinates.outputs["Normal"], mapping.inputs["Vector"])
tree.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
background = tree.nodes.get("Background")
tree.links.new(env.outputs["Color"], background.inputs["Color"])
background.inputs["Strength"].default_value = .52

def light(name, position, target, color, energy, kind, size):
    data = bpy.data.lights.new(name, kind)
    data.color = color
    data.energy = energy
    if kind == "AREA":
        data.shape = "DISK"
        data.size = size
    else:
        data.angle = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    aim(obj, target)

light("Low sun across field", (4, 3.6, 4.5), (0, 0, 1.1),
      (1, .73, .43), 2.35, "SUN", .075)
light("Open sky through canopy", (.82, -1.28, 2.65), (0, -.10, 1.63),
      (.76, .85, 1), 48, "AREA", 1.38)
light("Warm meadow bounce", (-.66, -.87, 1.21), (0, -.05, 1.59),
      (1, .78, .56), 11, "AREA", .85)

ground, shader = material("Meadow earth and short grass", (.16, .21, .065), .92)
tree = ground.node_tree
noise = tree.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 1.3
ramp = tree.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = .22
ramp.color_ramp.elements[0].color = (.09, .111, .029, 1)
ramp.color_ramp.elements[1].position = .77
ramp.color_ramp.elements[1].color = (.29, .285, .083, 1)
geo = tree.nodes.new("ShaderNodeTexCoord")
tree.links.new(geo.outputs["Object"], noise.inputs["Vector"])
tree.links.new(noise.outputs["Fac"], ramp.inputs[0])
tree.links.new(ramp.outputs[0], shader.inputs["Base Color"])

def turf(x, y):
    return .69 + .085 * sin(y * .33 + x * .23) + .045 * sin(x * .8)

vertices, faces = [], []
for j in range(54):
    for i in range(53):
        x, y = (i - 26) * .82, j * .86 - 4.3
        vertices.append((x, y, turf(x, y)))
        if i and j:
            a = j * 53 + i
            faces.append((a-54, a-53, a, a-1))
land = mesh("Rolling orchard meadow", vertices, faces, ground)
for polygon in land.data.polygons:
    polygon.use_smooth = True

before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(ENV / "grass/grass_medium_01_1k.gltf"))
imported = sorted((obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"),
                  key=lambda obj: obj.name)
sources, tall_sources = [], []
bpy.context.view_layer.update()
for obj in imported:
    if obj.dimensions.z > .12 and len(obj.data.polygons) > 100:
        data = obj.data.copy()
        transform = obj.matrix_world.copy()
        center = sum((Vector(point) for point in obj.bound_box), Vector()) / 8
        center.z = 0
        transform.translation = -(transform.to_3x3() @ center)
        data.transform(transform)
        sources.append(data)
        if obj.dimensions.z > .36:
            tall_sources.append(data)
    obj.hide_render = True
    obj.hide_viewport = True

def gust(time, lag=0):
    phase = (time - 1.0 - lag) / 1.7
    return sin(pi * phase)**1.2 if 0 < phase < 1 else 0

for n in range(221):
    at_edge = n >= 205
    if at_edge:
        y = rng.uniform(2.9, 4.8)
        x = -.34*y + rng.uniform(.48, .92)
        variants = tall_sources or sources
    else:
        y = rng.uniform(1.4, 12)
        x = rng.uniform(-.48*y - 1.1, -.25*y + 2.1)
        variants = sources
    obj = bpy.data.objects.new("Meadow tuft", variants[n % len(variants)])
    scene.collection.objects.link(obj)
    obj.location = (x, y, turf(x,y) - .02)
    scale = rng.uniform(.73, 1.65)
    height = rng.uniform(1.33, 1.72) if at_edge else 1
    obj.scale = (scale, scale, scale * height)
    azimuth = rng.uniform(-pi, pi)
    lag = .055 * (x + .4*y) + .025 * (y - 3)
    if y < 7.3:
        obj.rotation_mode = "QUATERNION"
        facing = Quaternion((0, 0, 1), azimuth)
        for frame in (*range(1, 48, 3), 48):
            t = (frame - 1) / 12
            bend = gust(t, lag) * (.16 + .075*sin(11*t - x*2))
            lean = Euler((.013*sin(3*t + n) + bend*.42, bend, 0)).to_quaternion()
            obj.rotation_quaternion = lean @ facing
            obj.keyframe_insert(data_path="rotation_quaternion", frame=frame)
    else:
        obj.rotation_euler.z = azimuth

def autumn_leaf(name, length, color):
    mat, shader = material(name, color, .51)
    shader.inputs["Subsurface Weight"].default_value = .055
    shader.inputs["Subsurface Scale"].default_value = .008
    vein, _ = material(name + " veins", tuple(c*.50 for c in color), .66)
    vertices, faces = [], []
    for row in range(15):
        v = row / 14
        width = max(.008, sin(pi*v)**.84) * (.30 + .032*cos(v*10*pi)) * length
        for col in range(5):
            u = (col-2) / 2
            vertices.append((u*width + .06*length*sin(pi*v), length*(v-.45),
                             length*(.18*(v-.42)**2 + .084*abs(u)*sin(pi*v)
                                     + .032*u*sin(v*6))))
        if row:
            for col in range(4):
                k = row*5 + col
                faces.append((k-5, k-4, k+1, k))
    leaf = mesh(name, vertices, faces, mat)
    for polygon in leaf.data.polygons:
        polygon.use_smooth = True
    path = bpy.data.curves.new(name + " midrib", "CURVE")
    path.dimensions = "3D"
    path.bevel_depth = length*.009
    centerline = path.splines.new("POLY")
    centerline.points.add(14)
    for row, point in enumerate(centerline.points):
        x, y, z = vertices[row*5+2]
        point.co = (x, y, z + length*.006, 1)
    rib = bpy.data.objects.new(path.name, path)
    scene.collection.objects.link(rib)
    path.materials.append(vein)
    rib.parent = leaf
    return leaf

def drift(obj, x, y, z, start, speed, phase):
    for frame in range(1, 49):
        t = (frame-1)/12
        age = t - start
        flutter = max(0, age)
        obj.location = (x + .107*flutter + .048*sin(flutter*4+phase)*min(1, flutter*4),
                        y + .085*sin(flutter*2.7+phase)*min(1, flutter*4),
                        z - speed*age + .019*sin(flutter*6+phase)*min(1, flutter*4))
        obj.rotation_euler = (1.38 + .47*sin(5.2*flutter+phase), .52*sin(4.2*flutter),
                              .6 + flutter*2.2 + .25*sin(6*flutter+phase))
        obj.keyframe_insert(data_path="location", frame=frame)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)

rng.seed(618)
hero = autumn_leaf("Copper leaf", .048, (.52, .166, .032))
drift(hero, .165, -.36, 1.800, .97, .142, .55)
for i in range(9):
    depth = rng.uniform(.45, 3.1)
    leaf = autumn_leaf("Falling oak leaf %02d" % i, rng.uniform(.036, .077),
                       rng.choice([(.37, .084, .019), (.55, .238, .043), (.34, .30, .055)]))
    x = rng.uniform(.25, .83) - depth*.32
    release = rng.uniform(.96, 1.97)
    speed = rng.uniform(.16, .39)
    # Start above the gate and let the leaf enter naturally as it falls.
    top_ray = camera.rotation_euler.to_matrix() @ Vector(
        (0, .54 * camera_data.sensor_width * 360 / (camera_data.lens * 640), -1))
    top_z = camera.location.z + (depth - camera.location.y) * top_ray.z / top_ray.y
    drift(leaf, x, depth, top_z, release, speed, rng.uniform(0, 6.2))

for frame, name in [(1, "Watching"), (13, "Breeze"), (16, "Gaze catches leaf"),
                    (19, "Head follows"), (32, "Wind settles"), (34, "Blink"), (43, "Release")]:
    scene.timeline_markers.new(name, frame=frame)
scene.frame_set(1)
