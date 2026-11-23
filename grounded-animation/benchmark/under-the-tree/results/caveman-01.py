"""Under the Tree. Build in Blender background mode with --python scene.py."""
from pathlib import Path
from math import sin, cos, pi, exp, radians
import random

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ENV = ASSETS / "environment"
rng = random.Random(171)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "Under the Tree"
scene["Character base"] = "Einar Rig (CC BY 4.0) Blender Foundation | studio.blender.org"
scene["Environment textures"] = "Jolcham Oak Bark by Charlotte Baglioni, Poly Haven (CC0)"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.eevee.taa_render_samples = 24

with bpy.data.libraries.load(str(ASSETS / "einar.blend"), link=False) as (_, target):
    target.collections = ["CH-einar"]
actor = target.collections[0]
actor.name = "Rowan • Character"
scene.collection.children.link(actor)
rig = bpy.data.objects["RIG-einar"]
rig.animation_data.action = None
# Move the character and all independent rig helpers together.
seat = bpy.data.objects.new("Seated staging", None)
actor.objects.link(seat)
actor_objects = set(actor.all_objects)
for obj in actor_objects - {seat}:
    if obj.parent not in actor_objects:
        obj.parent = seat
seat.location.z = -.64


def material(name, color, roughness=.8):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return mat, shader


def fabric(name, colors, scale):
    mat, shader = material(name, colors[0], .91)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    coord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 3
    links.new(coord.outputs["Object"], noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    for element, color in zip(ramp.color_ramp.elements, colors):
        element.color = (*color, 1)
    links.new(noise.outputs["Fac"], ramp.inputs[0])
    links.new(ramp.outputs[0], shader.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .24
    bump.inputs["Distance"].default_value = .00055
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs[0], shader.inputs["Normal"])
    shader.inputs["Sheen Weight"].default_value = .25
    return mat


coat = fabric("Rowan • slate waxed canvas", ((.018, .036, .032), (.063, .11, .095)), 820)
lining = fabric("Rowan • russet collar", ((.054, .017, .009), (.16, .07, .033)), 650)
knit = fabric("Rowan • oatmeal wool", ((.10, .09, .064), (.28, .22, .147)), 950)
for part, mat in (("jacket_main", coat), ("jacket_collar1", lining),
                  ("jacket_collar2", lining), ("sweater", knit)):
    slots = bpy.data.objects["GEO-einar_" + part].data.materials
    for i in range(len(slots)):
        slots[i] = mat
bpy.data.objects["GEO-einar_hat"].hide_render = True

# Use the shared rig's groom attachments with a new hair palette.
hair = bpy.data.materials["einar.hair"]
hair_nodes = hair.node_tree.nodes
hair_links = hair.node_tree.links
out = next(n for n in hair_nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output)
hair_shader = hair_nodes.new("ShaderNodeBsdfPrincipled")
hair_shader.inputs["Roughness"].default_value = .53
strand = hair_nodes.new("ShaderNodeHairInfo")
tones = hair_nodes.new("ShaderNodeValToRGB")
tones.color_ramp.elements[0].color = (.012, .008, .006, 1)
tones.color_ramp.elements[1].color = (.125, .073, .043, 1)
tones.color_ramp.elements.new(.88).color = (.045, .025, .016, 1)
hair_links.new(strand.outputs["Random"], tones.inputs[0])
hair_links.new(tones.outputs[0], hair_shader.inputs["Base Color"])
hair_links.new(hair_shader.outputs[0], out.inputs["Surface"])


def pose(name, channel, samples):
    bone = rig.pose.bones[name]
    if channel == "rotation_euler":
        bone.rotation_mode = "XYZ"
    for frame, value in samples:
        setattr(bone, channel, value)
        bone.keyframe_insert(channel, frame=frame, group=name)


pose("MSTR-TGT-Eyes", "location", [
    (1, (-.045, 0, .021)), (12, (-.044, 0, .020)),
    (14, (.10, 0, .105)), (16, (.214, 0, .112)), (20, (.249, 0, .053)),
    (26, (.288, 0, -.034)), (32, (.332, 0, -.092)),
    (36, (.332, 0, -.092)), (39, (.29, 0, -.101)), (48, (.284, 0, -.105)),
])
pose("FK-Head", "rotation_euler", [
    (1, (radians(1), radians(3.0), radians(-3.2))),
    (16, (radians(1), radians(3.0), radians(-3.2))),
    (23, (radians(.8), radians(-1.9), radians(-2.6))),
    (32, (radians(-1.0), radians(-4.0), radians(-2.1))),
    (39, (radians(-1.45), radians(-3.7), radians(-2.3))),
    (48, (radians(-1.40), radians(-3.7), radians(-2.3))),
])
pose("MSTR-Spine_Chest", "rotation_euler", [
    (1, (.013, 0, -.025)), (13, (.019, 0, -.024)),
    (28, (.013, 0, -.026)), (43, (.018, 0, -.024)), (48, (.017, 0, -.024)),
])
for side, sign in (("L", 1), ("R", -1)):
    pose("ACT-Eyebrow_Inner." + side, "location", [
        (1, (-sign * .0015, -.0021, 0)), (12, (-sign * .0015, -.0021, 0)),
        (17, (-sign * .0011, -.0006, 0)), (29, (-sign * .0014, -.0018, 0)),
        (40, (-sign * .0007, -.0008, 0)), (48, (-sign * .0007, -.0008, 0)),
    ])
    pose("Blink." + side, "location", [
        (1, (0, -.00045, 0)), (15, (0, .0002, 0)),
        (32, (0, -.00035, 0)), (34, (0, -.00045, 0)),
        (35, (0, -.006, 0)), (36, (0, -.00265, 0)),
        (38, (0, -.0003, 0)), (48, (0, -.00035, 0)),
    ])
    pose("ACT-Mouth_Corner." + side, "location", [
        (1, (-.00135, -.00055, .0002)), (31, (-.00135, -.00055, .0002)),
        (36, (-.0011, -.00036, .00012)), (42, (.00005, -.00012, 0)),
        (48, (.00005, -.00012, 0)),
    ])
pose("MSTR-Jaw", "rotation_euler", [(1, (.006, 0, 0)), (33, (.006, 0, 0)),
                                   (41, (-.005, 0, 0)), (48, (-.005, 0, 0))])


def mesh(name, vertices, faces, materials=()):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    for mat in materials:
        data.materials.append(mat)
    return obj


bark, bark_shader = material("Oak • weathered bark", (.16, .104, .064), .91)
nodes, links = bark.node_tree.nodes, bark.node_tree.links
for filename in ("oak_bark_diffuse.jpg", "oak_bark_normal.jpg"):
    image = bpy.data.images.load(str(ENV / filename))
    image.pack()
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    if "normal" in filename:
        image.colorspace_settings.name = "Non-Color"
        normal = nodes.new("ShaderNodeNormalMap")
        normal.inputs["Strength"].default_value = .85
        links.new(tex.outputs["Color"], normal.inputs["Color"])
        links.new(normal.outputs[0], bark_shader.inputs["Normal"])
    else:
        links.new(tex.outputs["Color"], bark_shader.inputs["Base Color"])


def timber(name, start, end, bottom, top, segments=80):
    start, end = Vector(start), Vector(end)
    axis = (end - start).normalized()
    side = Vector((1, 0, 0))
    if abs(axis.dot(side)) > .9:
        side = Vector((0, 1, 0))
    across = axis.cross(side).normalized()
    side = across.cross(axis)
    rings = 23
    vertices, faces = [], []
    for j in range(rings):
        t = j / (rings - 1)
        center = start.lerp(end, t) + side * (.037 * sin(pi * t))
        radius = bottom * (1 - t) + top * t
        for k in range(segments):
            a = k * 2 * pi / segments
            ripple = 1 + .051 * sin(9 * a + 1.7 * t) + .026 * sin(19 * a - t)
            ripple += .044 * sin(4 * a + t)
            flare = 1 + .30 * exp(-t * 18) * (.5 + .5 * cos(5 * a))
            vertices.append(center + (side * cos(a) + across * sin(a)) * radius * ripple * flare)
    for j in range(rings - 1):
        for k in range(segments):
            p, q = j * segments + k, j * segments + (k + 1) % segments
            faces.append((p, q, q + segments, p + segments))
    obj = mesh(name, vertices, faces, [bark])
    uv = obj.data.uv_layers.new()
    repeats = max(1, round(2 * pi * bottom / .7))
    for poly in obj.data.polygons:
        poly.use_smooth = True
        j, k = divmod(poly.index, segments)
        u, v = k * repeats / segments, j / (rings - 1) * (end - start).length / .78
        du, dv = repeats / segments, (end - start).length / (.78 * (rings - 1))
        for loop, coords in zip(poly.loop_indices, ((u, v), (u + du, v),
                                                     (u + du, v + dv), (u, v + dv))):
            uv.data[loop].uv = coords
    return obj


timber("Oak trunk", (.26, .49, -.15), (.30, .57, 4.1), .46, .33)
timber("Oak bough", (.28, .55, 2.25), (-2.4, .60, 3.1), .25, .075, 40)
timber("Oak fork", (-1.28, .59, 2.8), (-2.12, -.54, 3.65), .105, .038, 32)


def ground(x, y):
    return (.052 * sin(x * .8 + y * .35) + .039 * cos(y * 1.4)
            + .83 * (1 - exp(-max(0, y) * .045))
            + .40 * exp(-((y - 17) / 6) ** 2) * sin(.43 * x + .8))


earth, earth_shader = material("Meadow • dry grass and earth", (.19, .21, .07))
nodes, links = earth.node_tree.nodes, earth.node_tree.links
noise = nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 5.3
noise.inputs["Detail"].default_value = 4
coord = nodes.new("ShaderNodeTexCoord")
links.new(coord.outputs["Object"], noise.inputs[0])
ramp = nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (.048, .060, .022, 1)
ramp.color_ramp.elements[1].color = (.33, .278, .079, 1)
links.new(noise.outputs["Fac"], ramp.inputs[0])
links.new(ramp.outputs[0], earth_shader.inputs["Base Color"])
grid = 111
verts = [(x := (i - 55) * .46, y := j * .46 - 4, ground(x, y))
         for j in range(grid) for i in range(grid)]
faces = [(p, p + 1, p + grid + 1, p + grid)
         for j in range(grid - 1) for i in range(grid - 1) for p in [j * grid + i]]
terrain = mesh("Rolling field", verts, faces, [earth])
terrain.data.polygons.foreach_set("use_smooth", [True] * len(faces))

grass_colors = [(.089, .132, .034), (.17, .215, .059), (.27, .278, .076),
                (.38, .306, .093), (.47, .407, .168), (.31, .236, .083)]
grass_mats = []
for i, color in enumerate(grass_colors):
    mat, shader = material("Meadow blade %02d" % i, color, .86)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    transmission = nodes.new("ShaderNodeBsdfTranslucent")
    transmission.inputs[0].default_value = (*color, 1)
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = .36
    links.new(shader.outputs[0], mix.inputs[1])
    links.new(transmission.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], nodes.get("Material Output").inputs[0])
    grass_mats.append(mat)

# Each strip of meadow gets a delayed bend. Blade roots stay pinned.
for zone in range(10):
    verts, faces, bend, indices = [], [], [], []
    for clump in range(270):
        x = -.23 - zone * .67 - rng.random() * .67
        y = .42 + rng.random() ** 1.65 * 11.0
        hot = .5 + .5 * sin(4.4 * x + 1.8 * y)
        size = rng.uniform(.19, .53) * (.85 + hot * .32)
        if clump % 9 == 0:
            size *= 1.48
        for blade in range(rng.randint(4, 8)):
            xx, yy = x + rng.uniform(-.095, .095), y + rng.uniform(-.095, .095)
            zz = ground(xx, yy) - .012
            a = rng.random() * 2 * pi
            h, w = size * rng.uniform(.53, 1.32), rng.uniform(.005, .014)
            dx, dy = cos(a), sin(a)
            lean = rng.uniform(.13, .47) * h
            offset = len(verts)
            for t, profile in ((0, .63), (.34, 1), (.72, .65), (1, .025)):
                for s in (-1, 1):
                    point = Vector((xx + dx * lean * t*t - dy * w * s * profile,
                                    yy + dy * lean * t*t + dx * w * s * profile,
                                    zz + h * t))
                    verts.append(point)
                    bend.append(point + Vector((-h * .39, h * .11, -h * .11)) * t*t)
            color = rng.choices(range(6), [12, 21, 20, 11, 4, 6])[0]
            for b in range(0, 6, 2):
                faces.append((offset+b, offset+b+1, offset+b+3, offset+b+2))
                indices.append(color)
    plants = mesh("Wind strip %02d" % zone, verts, faces, grass_mats)
    plants.data.polygons.foreach_set("material_index", indices)
    plants.shape_key_add(name="Rest")
    gust = plants.shape_key_add(name="Wind bend")
    gust.data.foreach_set("co", [v for co in bend for v in co])
    delay = zone * 1.27
    for frame in range(1, 49):
        t = frame - delay
        envelope = exp(-((t - 20) / 7.2) ** 2)
        value = .036 + envelope * (.50 + .32 * sin((t - 12) * .64))
        value += .033 * sin(frame * .39 + zone * .5) * exp(-((frame-30)/14) ** 2)
        gust.value = value
        gust.keyframe_insert("value", frame=frame)

# Irregular hedgerow shapes break up the late-afternoon horizon.
hedge_mats = [material("Distant canopy %s" % i, c)[0] for i, c in enumerate(
    ((.10, .16, .088), (.151, .185, .094), (.205, .206, .102), (.25, .207, .10)))]
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2)
prototype = bpy.context.object
crown_data = prototype.data
for mat in hedge_mats:
    crown_data.materials.append(mat)
for poly in crown_data.polygons:
    poly.use_smooth = True
    poly.material_index = rng.choices(range(4), [4, 5, 3, 2])[0]
for i in range(110):
    x = rng.uniform(-23, 4)
    y = 15 + rng.uniform(0, 9)
    z = ground(x, y)
    obj = bpy.data.objects.new("Hedgerow crown", crown_data)
    scene.collection.objects.link(obj)
    obj.location = (x, y, z + rng.uniform(.12, .61))
    obj.scale = (rng.uniform(.34, 1.04), rng.uniform(.43, 1.06), rng.uniform(.25, .73))
    obj.rotation_euler.z = rng.random() * pi
bpy.data.objects.remove(prototype, do_unlink=True)

world = bpy.data.worlds.new("Open sky")
scene.world = world
world.use_nodes = True
nodes, links = world.node_tree.nodes, world.node_tree.links
bg = nodes.get("Background")
coord = nodes.new("ShaderNodeTexCoord")
split = nodes.new("ShaderNodeSeparateXYZ")
links.new(coord.outputs["Normal"], split.inputs[0])
ramp = nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = .01
ramp.color_ramp.elements[0].color = (.67, .66, .55, 1)
ramp.color_ramp.elements[1].position = .46
ramp.color_ramp.elements[1].color = (.25, .43, .60, 1)
links.new(split.outputs["Z"], ramp.inputs[0])
links.new(ramp.outputs[0], bg.inputs[0])
bg.inputs[1].default_value = .72


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area(name, position, target, power, color, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.color, data.shape, data.size = power, color, "DISK", size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    aim(obj, target)
    return data


area("Sky through canopy", (-1.55, -1.58, 2.68), (0, 0, 1.02), 145, (.78, .87, 1), 2.45)
area("Field bounce", (.84, -1.30, .78), (0, 0, 1.04), 28, (1, .80, .61), 1.80).use_shadow = False
area("Late light at edge of shade", (-1.0, .72, 1.72), (0, 0, 1.03), 48,
     (1, .65, .37), .86).use_shadow = False
sun = bpy.data.lights.new("Low sun over the field", "SUN")
sun.energy, sun.angle, sun.color = 2.25, .10, (1, .78, .52)
sun_obj = bpy.data.objects.new(sun.name, sun)
scene.collection.objects.link(sun_obj)
sun_obj.location = (5, 6, 3.7)
aim(sun_obj, (0, 0, .4))

camera = bpy.data.objects.new("Locked portrait", bpy.data.cameras.new("Portrait glass"))
scene.collection.objects.link(camera)
scene.camera = camera
camera.location = (.405, -1.38, 1.039)
aim(camera, (-.071, -.103, .995))
camera.data.lens = 87
camera.data.dof.use_dof = True
camera.data.dof.focus_distance = 1.298
camera.data.dof.aperture_fstop = 5.0
camera.data.dof.aperture_blades = 8

# Curved autumn leaves have a center rib and asymmetric margins.
leaf_mats = [material("Fallen leaf • " + name, rgb, .69)[0] for name, rgb in (
    ("copper", (.45, .13, .024)), ("ochre", (.56, .284, .043)),
    ("umber", (.235, .070, .020)), ("rib", (.36, .155, .032)))]
bpy.context.view_layer.update()
camera_rotation = camera.rotation_euler.to_matrix()
screen_right = camera_rotation @ Vector((1, 0, 0))
screen_up = camera_rotation @ Vector((0, 1, 0))
forward = camera_rotation @ Vector((0, 0, -1))


def falling_leaf(index, length, depth, start, end, horizontal, drift, tint):
    verts, faces = [], []
    for j in range(17):
        t = j / 16
        width = length * (.25 * sin(pi*t) ** .85 + .006)
        width *= 1 + .19 * sin(t * 7 * pi)
        for k in range(-2, 3):
            u = k / 2
            verts.append((u * width * (1 - .12 * u) + .023 * length * sin(t*pi),
                          (t - .47) * length,
                          length * (.15 * (t - .43)**2 + .079 * u*u * sin(t*pi)
                                    + .055 * u * sin(t*2*pi))))
    for j in range(16):
        for k in range(4):
            p = 5 * j + k
            faces.append((p, p + 1, p + 6, p + 5))
    leaf = mesh("Tracked copper leaf" if index == 0 else "Falling leaf %d" % index,
                verts, faces, leaf_mats)
    for poly in leaf.data.polygons:
        poly.material_index = tint
        poly.use_smooth = True
    rib_verts, rib_faces = [], []
    for j in range(17):
        x, y, z = verts[5*j + 2]
        rib_verts.extend(((x - .015 * length, y, z + .00025),
                          (x + .015 * length, y, z + .00025)))
        if j:
            p = 2*j
            rib_faces.append((p - 2, p - 1, p + 1, p))
    rib = mesh("Leaf midrib", rib_verts, rib_faces, [leaf_mats[3]])
    rib.parent = leaf

    for frame in range(1, 49):
        t = (frame - start) / (end - start)
        phase = frame * (.31 + index * .018) + index
        flutter = sin(phase) * .014 + sin(phase * .43) * .012
        projected_x = horizontal + drift * t + flutter
        projected_y = .19 - .40 * t + .006 * sin(phase * 1.3)
        pos = camera.location + forward * (depth + .065 * sin(phase * .42))
        pos += screen_right * projected_x * depth / 1.35
        pos += screen_up * projected_y * depth / 1.35
        leaf.location = pos
        leaf.rotation_euler = (1.09 + .81 * sin(phase),
                               .64 * cos(phase * .74),
                               phase * .56 + .9 * sin(phase * .44))
        leaf.keyframe_insert("location", frame=frame)
        leaf.keyframe_insert("rotation_euler", frame=frame)


falling_leaf(0, .025, 1.015, 10, 51, -.151, -.073, 0)
falling_leaf(1, .045, 2.34, 14, 57, -.233, .030, 1)
falling_leaf(2, .054, 2.75, 17, 54, -.111, -.116, 2)
falling_leaf(3, .036, 1.85, 25, 67, -.265, .073, 1)
falling_leaf(4, .055, 2.95, 31, 75, -.182, -.095, 0)

for frame, name in ((1, "Watching"), (13, "Breeze gathers"),
                    (15, "Eyes catch the leaf"), (19, "Head follows"),
                    (33, "Wind eases"), (35, "Blink"), (42, "Hold")):
    scene.timeline_markers.new(name, frame=frame)

scene.frame_set(1)
bpy.context.view_layer.update()
