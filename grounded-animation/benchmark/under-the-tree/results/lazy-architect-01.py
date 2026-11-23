"""Under the Tree. Run with Blender in background mode using --python scene.py.

Character foundation: Einar Rig by Blender Foundation | studio.blender.org,
CC BY 4.0. Adapted for this shot with a new silhouette, palette and performance.
Oak maps and Autumn Meadow HDRI: Poly Haven, CC0.
"""
from pathlib import Path
from math import cos, exp, pi, sin
from random import Random

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ENV = ASSETS / "environment"
rng = Random(39)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'
scene.eevee.taa_render_samples = 48

with bpy.data.libraries.load(str(ASSETS / "einar.blend"), link=False) as (_, target):
    target.collections = ["CH-einar"]
scene.collection.children.link(target.collections[0])
target.collections[0].name = "Rowan | field surveyor"
rig = bpy.data.objects["RIG-einar"]

def material(name, color, roughness=0.7):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return mat, shader

def grain(mat, shader, scale, distance):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    noise = nodes.new("ShaderNodeTexNoise")
    links.new(nodes.new("ShaderNodeTexCoord").outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = scale
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.28
    bump.inputs["Distance"].default_value = distance
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return noise

def mesh(name, verts, faces, mats):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    for mat in mats:
        data.materials.append(mat)
    return obj

def source_image(path, noncolor=False):
    image = bpy.data.images.load(str(path))
    if noncolor:
        image.colorspace_settings.name = "Non-Color"
    image.pack()
    return image

# Adapt the supplied sculpt and groom into Rowan. Keep the eyelid contact
# geometry intact while giving the nose and cheeks a different profile.
for name in ("hat", "mustache", "mustache.messy", "beard.messy"):
    bpy.data.objects["GEO-einar_" + name].hide_render = True
head = bpy.data.objects["GEO-einar_head"]
for block in head.data.shape_keys.key_blocks:
    for point in block.data:
        x, y, z = point.co
        nose = exp(-((x / .019)**2 + ((z - 1.600) / .022)**2 + ((y + .158) / .035)**2))
        cheek = exp(-(((abs(x) - .059) / .029)**2 + ((z - 1.594) / .033)**2 + ((y + .11) / .047)**2))
        point.co.y += .008 * nose - .003 * cheek
        point.co.x += x * .14 * cheek
coat, fabric = material("Petrol blue brushed canvas", (.037, .089, .089))
grain(coat, fabric, 420, .0008)
fabric.inputs["Sheen Weight"].default_value = .24
lining, fabric = material("Faded slate collar", (.070, .105, .101))
grain(lining, fabric, 520, .0006)
fabric.inputs["Sheen Weight"].default_value = .3
for part, mat in (("jacket_main", coat), ("jacket_collar1", lining), ("jacket_collar2", lining)):
    slots = bpy.data.objects["GEO-einar_" + part].data.materials
    for index in range(len(slots)):
        slots[index] = mat
hair, hair_shader = material("Dark chestnut with silver strands", (.082, .039, .018), .49)
nodes, links = hair.node_tree.nodes, hair.node_tree.links
strand = nodes.new("ShaderNodeHairInfo")
palette = nodes.new("ShaderNodeValToRGB")
palette.color_ramp.elements[0].color = (.018, .009, .006, 1)
palette.color_ramp.elements[1].color = (.14, .083, .048, 1)
palette.color_ramp.elements.new(.90).color = (.068, .033, .016, 1)
links.new(strand.outputs["Random"], palette.inputs[0])
links.new(palette.outputs[0], hair_shader.inputs["Base Color"])
for part in ("hair", "hair.messy", "beard", "eyebrows"):
    bpy.data.objects["GEO-einar_" + part].data.materials[0] = hair

def bone_keys(name, channel, poses):
    bone = rig.pose.bones[name]
    for frame, value in poses:
        setattr(bone, channel, value)
        bone.keyframe_insert(data_path=channel, frame=frame, group=name)

bone_keys("MSTR-TGT-Eyes", "location", [
    (1, (-.135, 0, .027)), (12, (-.135, 0, .027)),
    (15, (-.225, 0, .061)), (18, (-.291, 0, .057)),
    (24, (-.329, 0, .019)), (31, (-.354, 0, -.044)),
    (36, (-.337, 0, -.093)), (48, (-.327, 0, -.111))])
bone_keys("FK-Head", "rotation_euler", [
    (1, (.018, .029, -.045)), (17, (.017, .029, -.045)),
    (22, (.014, .058, -.052)), (30, (.029, .098, -.041)),
    (37, (.065, .111, -.041)), (45, (.074, .109, -.041)), (48, (.074, .109, -.041))])
for side, sign in (("L", 1), ("R", -1)):
    bone_keys("ACT-Eyebrow_Inner." + side, "location", [
        (1, (-sign * .0014, -.0028, 0)), (14, (-sign * .0014, -.0028, 0)),
        (23, (-sign * .001, -.0014, 0)), (37, (-sign * .0005, -.0008, 0)),
        (48, (-sign * .0005, -.0008, 0))])
    bone_keys("ACT-Mouth_Corner." + side, "location", [
        (1, (-sign * .0016, -sign * .0014, 0)),
        (32, (-sign * .0016, -sign * .0014, 0)),
        (40, (sign * .0002, 0, 0)), (48, (sign * .0002, 0, 0))])
    bone_keys("Blink." + side, "location", [
        (1, (0, -.0005, 0)), (33, (0, -.0005, 0)),
        (34, (0, -.0034, 0)), (35, (0, -.006, 0)),
        (37, (0, -.0012, 0)), (39, (0, -.0005, 0)), (48, (0, -.0005, 0))])
bone_keys("MSTR-Jaw", "rotation_euler", [
    (1, (.003, 0, 0)), (32, (.003, 0, 0)), (43, (.010, 0, 0)), (48, (.010, 0, 0))])
for frame, rise in [(1, 0), (14, .0016), (29, -.0004), (43, .001), (48, .0007)]:
    rig.location.z = rise
    rig.keyframe_insert(data_path="location", frame=frame)

# Oak trunk wraps just behind the near shoulder. Give the ridges both
# geometric depth and a finer tangent-space normal.
bark, bark_shader = material("Old oak | furrowed bark", (.11, .070, .038), .91)
nodes, links = bark.node_tree.nodes, bark.node_tree.links
for file, socket in (("oak_bark_diffuse.jpg", "Base Color"), ("oak_bark_normal.jpg", "Normal")):
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = source_image(ENV / file, socket == "Normal")
    output = tex.outputs["Color"]
    if socket == "Normal":
        normal = nodes.new("ShaderNodeNormalMap")
        normal.inputs["Strength"].default_value = .85
        links.new(output, normal.inputs["Color"])
        output = normal.outputs["Normal"]
    links.new(output, bark_shader.inputs[socket])

def trunk(name, length, center, radius):
    sides, rings = 96, 36
    verts, faces = [], []
    for j in range(rings + 1):
        t = j / rings
        x, y, z = center(t)
        for i in range(sides):
            a = i * 2 * pi / sides
            ridge = .010 * sin(19 * a + 2.3 * t) + .009 * sin(11 * a - 4 * t)
            r = radius(t) + ridge + .016 * sin(5 * a + t)
            verts.append((x + r * cos(a), y + .88 * r * sin(a), z))
    for j in range(rings):
        for i in range(sides):
            a = j * sides + i
            b = j * sides + (i + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    obj = mesh(name, verts, faces, [bark])
    uv = obj.data.uv_layers.new()
    for index, polygon in enumerate(obj.data.polygons):
        polygon.use_smooth = True
        i, j = index % sides, index // sides
        corners = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
        for loop, (u, v) in zip(polygon.loop_indices, corners):
            uv.data[loop].uv = (u * 2.5 / sides, v * length * 1.4 / rings)

trunk("Oak at the field edge", 4, lambda t: (-.355 - .23*t, .173 + .16*t, .43 + 4*t),
      lambda t: .305 - .14*t + .15*exp(-18*t))

def elevation(x, y):
    return .48 + .09*sin(.36*x + .22*y) + .12*sin(.28*y) + .29*exp(-((y-15)/6)**2)

earth, earth_shader = material("Mixed meadow cover", (.15, .17, .060), .92)
noise = grain(earth, earth_shader, 4.2, .12)
color = earth.node_tree.nodes.new("ShaderNodeValToRGB")
color.color_ramp.elements[0].position = .24
color.color_ramp.elements[0].color = (.071, .092, .026, 1)
color.color_ramp.elements[1].position = .76
color.color_ramp.elements[1].color = (.28, .255, .090, 1)
earth.node_tree.links.new(noise.outputs["Fac"], color.inputs[0])
earth.node_tree.links.new(color.outputs[0], earth_shader.inputs["Base Color"])
verts = [(x, y, elevation(x, y)) for y in range(-5, 54) for x in range(-32, 33)]
faces = [(j*65+i, j*65+i+1, (j+1)*65+i+1, (j+1)*65+i) for j in range(58) for i in range(64)]
ground = mesh("Rolling meadow", verts, faces, [earth])
for poly in ground.data.polygons:
    poly.use_smooth = True

grass = [material("Meadow leaf %s" % i, col)[0] for i, col in enumerate([
    (.19,.24,.068), (.26,.28,.083), (.38,.34,.124), (.105,.16,.037), (.45,.36,.133)])]
for strip in range(10):
    verts, faces, colors, bends = [], [], [], []
    for _ in range(110):
        x, y = rng.uniform(-5, 6), rng.uniform(.6, 4.2) + strip*.88
        base = elevation(x, y)
        for _ in range(rng.randrange(4, 9)):
            dx, dy = rng.uniform(-.085,.085), rng.uniform(-.085,.085)
            h = rng.uniform(.16,.58)
            w = rng.uniform(.008,.026)
            a = rng.uniform(0, 2*pi)
            sx, sy = cos(a)*w, sin(a)*w
            lx, ly = rng.uniform(-.20,.20), rng.uniform(-.16,.16)
            k = len(verts)
            for t, width in ((0,.45), (.45,1), (.78,.62), (1,0)):
                for side in (-1, 1):
                    verts.append((x+dx+lx*t*t+sx*width*side, y+dy+ly*t*t+sy*width*side,
                                  base+h*t-.02))
                    bends.append((t*t*h, sin(x*1.7 + y*.75)))
            faces.extend((k+n,k+n+1,k+n+3,k+n+2) for n in (0,2,4))
            colors.extend([rng.randrange(len(grass))]*3)
    plants = mesh("Wind through field | %02d" % strip, verts, faces, grass)
    for face, color_index in zip(plants.data.polygons, colors):
        face.material_index = color_index
    plants.shape_key_add(name="Rest")
    bend = plants.shape_key_add(name="Gust bends rooted blades")
    for point, (weight, phase) in zip(bend.data, bends):
        point.co.x += weight*(.55+.19*phase)
        point.co.y += weight*.26
        point.co.z -= weight*.17
    delay = strip*.85
    for frame, amplitude in ((1,.04),(11,.04),(15+delay,.23),(19+delay,.89),
                             (23+delay,.54),(27+delay,.71),(33+delay,.13),(43+delay,.03),(53+delay,.03)):
        bend.value = amplitude
        bend.keyframe_insert(data_path="value", frame=frame)

# A muted far hedgerow gives the narrow band of field a natural horizon.
hedge = [material("Hedgerow %d" % i, rgb)[0] for i, rgb in enumerate(
    [(.093,.117,.057), (.14,.155,.069), (.19,.18,.074), (.095,.127,.075)])]
for i in range(58):
    y = rng.uniform(27, 33)
    x = -26 + i*.92
    h = rng.uniform(.6, 2.3)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1,
                                         location=(x, y, elevation(x,y)+h*.49))
    crown = bpy.context.object
    crown.name = "Far hedgerow"
    crown.scale = (rng.uniform(.75,2.6), rng.uniform(.8,2), h)
    crown.data.materials.append(rng.choice(hedge))
    for poly in crown.data.polygons:
        poly.use_smooth = True

# Held portrait. Keep the near eye and far eye inside the same focal band.
camera_data = bpy.data.cameras.new("Portrait lens")
camera = bpy.data.objects.new("Held three-quarter close-up", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera.location = (.294, -.929, 1.679)
aim = Vector((.048, -.091, 1.648))
camera.rotation_euler = (aim-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.lens = 57
camera_data.dof.use_dof = True
camera_data.dof.focus_distance = .840
camera_data.dof.aperture_fstop = 5.0

world = bpy.data.worlds.new("Late afternoon open sky")
scene.world = world
world.use_nodes = True
nodes, links = world.node_tree.nodes, world.node_tree.links
sky = nodes.new("ShaderNodeTexEnvironment")
sky.image = source_image(ENV / "autumn_meadow_1k.hdr")
background = nodes.get("Background")
links.new(sky.outputs["Color"], background.inputs["Color"])
background.inputs["Strength"].default_value = .42

def light(name, kind, position, aim, power, color, size):
    data = bpy.data.lights.new(name, kind)
    data.energy = power
    data.color = color
    if kind == "SUN":
        data.angle = size
    else:
        data.shape = "DISK"
        data.size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector(aim)-obj.location).to_track_quat('-Z','Y').to_euler()

light("Low sunlight over the meadow", "SUN", (5,4,3.8), (0,0,1.15), 2.05, (1,.79,.53), .14)
light("Open sky through the canopy", "AREA", (1.0,-1.28,2.46), (0,-.08,1.63),
      43, (.80,.89,1), 1.65)
light("Field bounce", "AREA", (-.28,-.79,.83), (0,-.09,1.61),
      8, (1,.85,.66), 1.25)

# Serrated, cambered leaves with their own veins and independently falling paths.
leaf_colors = [(.43,.17,.027), (.55,.28,.046), (.26,.20,.036), (.34,.085,.022)]
leaves = []
for index, rgb in enumerate(leaf_colors):
    mat, shader = material("Dry oak leaf %d" % index, rgb, .47)
    shader.inputs["Subsurface Weight"].default_value = .08
    grain(mat, shader, 290, .0012)
    leaves.append(mat)
vein = material("Leaf vein", (.24,.12,.027))[0]
profile = [(0,0),(.10,.14),(.19,.10),(.26,.28),(.34,.22),(.44,.41),(.51,.29),
           (.61,.42),(.68,.26),(.77,.32),(.83,.17),(.90,.18),(1,0)]
right = camera.rotation_euler.to_matrix() @ Vector((1,0,0))
up = camera.rotation_euler.to_matrix() @ Vector((0,1,0))
forward = camera.rotation_euler.to_matrix() @ Vector((0,0,-1))

for index in range(9):
    hero = index == 0
    length = .044 if hero else rng.uniform(.055,.102)
    verts, faces = [], []
    for y,w in profile:
        verts.extend([(-w*length,(y-.5)*length,.002*sin(y*pi)),
                      (0,(y-.5)*length,.006*sin(y*pi)),
                      (w*length,(y-.5)*length,.001*sin(y*pi))])
    for j in range(len(profile)-1):
        k = j*3
        faces.extend([(k,k+1,k+4,k+3),(k+1,k+2,k+5,k+4)])
    leaf = mesh("Leaf Rowan follows" if hero else "Falling oak leaf %02d" % index,
                verts, faces, [leaves[index % len(leaves)], vein])
    stem = mesh("Leaf midrib", [(-.00045,(y-.5)*length,.006*sin(y*pi)+.0003)
                              for y,_ in profile] +
                              [(.00045,(y-.5)*length,.006*sin(y*pi)+.0003) for y,_ in profile],
                [(j,j+1,j+1+len(profile),j+len(profile)) for j in range(len(profile)-1)], [vein])
    stem.parent = leaf
    depth = 1.03 if hero else rng.uniform(1.43,3.4)
    start = 13 if hero else rng.randrange(10,33)
    duration = 30 if hero else rng.randrange(15,39)
    start_x = .101 if hero else rng.uniform(.04,.31)*depth
    phase = rng.uniform(0, 2*pi)
    for frame in range(1,50,2):
        t = (frame-start)/duration
        x = start_x + (.070 if hero else .12)*t + .016*sin(6*t+phase)
        y = (.178 if hero else .21*depth) - (.31 if hero else .52)*t + .011*sin(9*t)
        leaf.location = camera.location + forward*(depth+.10*t) + right*x + up*y
        leaf.rotation_euler = (1.25+.63*sin(8*t+phase), .72*sin(11*t), phase+4.5*t)
        leaf.keyframe_insert(data_path="location", frame=frame)
        leaf.keyframe_insert(data_path="rotation_euler", frame=frame)

scene.timeline_markers.new("Watch", frame=1)
scene.timeline_markers.new("Breeze", frame=13)
scene.timeline_markers.new("Settle", frame=32)
scene["Character source"] = "Einar Rig by Blender Foundation | studio.blender.org | CC BY 4.0"
scene.frame_set(1)
