"""Under the Tree. Build with Blender 5.2 in background mode."""
from pathlib import Path
from math import sin, cos, pi, exp, radians, tan
from random import Random

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ENV = ASSETS / "environment"
rng = Random(672)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "Under the Tree"
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'


def collection(name):
    group = bpy.data.collections.new(name)
    scene.collection.children.link(group)
    return group


def mesh(name, verts, faces, group, materials):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    group.objects.link(obj)
    for mat in materials:
        data.materials.append(mat)
    return obj


def surface(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat, bsdf


def tint(mat, color, strength=1):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    for bsdf in list(nodes):
        if bsdf.type != 'BSDF_PRINCIPLED':
            continue
        base = bsdf.inputs['Base Color']
        if not base.is_linked:
            base.default_value = (*color, 1)
            continue
        mix = nodes.new('ShaderNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = strength
        mix.inputs[2].default_value = (*color, 1)
        links.new(base.links[0].from_socket, mix.inputs[1])
        links.new(mix.outputs[0], base)


# The supplied production face is the deformation foundation for the watchman.
with bpy.data.libraries.load(str(ASSETS / "einar.blend"), link=False) as (_, target):
    target.collections = ['CH-einar']
actor = target.collections[0]
actor.name = "Marek | watchman"
actor['Rig credit'] = 'Einar Rig (CC BY 4.0) Blender Foundation | studio.blender.org'
scene.collection.children.link(actor)
rig = bpy.data.objects['RIG-einar']
wardrobe = bpy.data.collections.new("Source groom and cap")
actor.children.link(wardrobe)
wardrobe.hide_render = True
for obj in list(actor.all_objects):
    if obj.parent is None:
        obj.location.z -= .54
    is_groom = (obj.type == 'CURVES' and 'eyebrows' not in obj.name
                and 'eyelashes' not in obj.name)
    if is_groom or obj.name in ('GEO-einar_hat', 'GEO-eye.cornea.L', 'GEO-eye.cornea.R'):
        for group in list(obj.users_collection):
            group.objects.unlink(obj)
        wardrobe.objects.link(obj)

# Resculpt the neutral head through an additive key so the facial correctives
# and eyelid rig still work. The watchman has a narrow jaw and a broken bridge.
head = bpy.data.objects['GEO-einar_head']
identity = head.shape_key_add(name="Marek | facial proportions", from_mix=False)
for vertex in identity.data:
    x, y, z = vertex.co
    jaw = exp(-((z - 1.536) / .054)**2) * (1 - exp(-(x / .036)**2))
    bridge = exp(-((z - 1.643) / .025)**2 - (x / .017)**2)
    tip = exp(-((z - 1.632) / .016)**2 - (x / .020)**2)
    front = max(0, min(1, (-y - .100) / .043))
    temple = exp(-((z - 1.715) / .036)**2) * (1 - exp(-(x / .060)**2))
    vertex.co.x = x * (1 - .12 * jaw + .05 * temple) + .0035 * tip * front
    vertex.co.y = y - .009 * bridge * front
    vertex.co.z = z + .005 * jaw
identity.value = 1

tint(bpy.data.materials['einar.skin'], (.79, .67, .58), .70)
tint(bpy.data.materials['eyes.iris'], (.56, .82, .50))
for name in ('einar.jacket.canvas', 'einar.jacket.collar', 'einar.jacket.rim'):
    tint(bpy.data.materials[name], (.28, .57, .72))
tint(bpy.data.materials['einar.sweater'], (.72, .44, .27))


def bone_keys(name, channel, keys):
    bone = rig.pose.bones[name]
    if channel == 'rotation_euler':
        bone.rotation_mode = 'XYZ'
    for frame, val in keys:
        setattr(bone, channel, val)
        bone.keyframe_insert(data_path=channel, frame=frame, group=name)


bone_keys('FK-Head', 'rotation_euler', [
    (1, (radians(2), radians(2), radians(-2))),
    (18, (radians(2), radians(2), radians(-2))),
    (26, (radians(1), radians(6), radians(-1))),
    (33, (radians(-2), radians(8), radians(-1))),
    (48, (radians(-2.5), radians(7), radians(-1))),
])
bone_keys('MSTR-TGT-Eyes', 'location', [
    (1, (-.09, 0, .020)), (13, (-.09, 0, .020)),
    (16, (-.27, .015, .080)), (22, (-.34, .020, .025)),
    (29, (-.36, .015, -.083)), (34, (-.31, 0, -.145)),
    (39, (-.25, 0, -.107)), (48, (-.25, 0, -.105)),
])
for side, sign in [('L', 1), ('R', -1)]:
    bone_keys('Blink.' + side, 'location', [
        (1, (0, 0, 0)), (33, (0, 0, 0)), (35, (0, -.006, 0)),
        (36, (0, -.004, 0)), (38, (0, 0, 0)), (48, (0, 0, 0)),
    ])
    bone_keys('ACT-Eyebrow_Inner.' + side, 'location', [
        (1, (-sign * .0008, -.0015, 0)), (28, (-sign * .0006, -.0011, 0)),
        (39, (0, -.0006, 0)), (48, (0, -.0006, 0)),
    ])
    bone_keys('ACT-Mouth_Corner.' + side, 'location', [
        (1, (-sign * .0012, .0007, 0)), (32, (-sign * .0012, .0007, 0)),
        (40, (0, -.0003, 0)), (48, (0, -.0003, 0)),
    ])
for frame, z in [(1, -.540), (12, -.5387), (26, -.5402), (38, -.5389), (48, -.540)]:
    rig.location.z = z
    rig.keyframe_insert(data_path='location', index=2, frame=frame)

woodland = collection("Oak and meadow")
bark, bark_bsdf = surface("Oak | furrowed bark", (.12, .07, .035), .91)
nodes, links = bark.node_tree.nodes, bark.node_tree.links
uv = nodes.new('ShaderNodeTexCoord')
for filename in ['oak_bark_diffuse.jpg', 'oak_bark_normal.jpg']:
    image = nodes.new('ShaderNodeTexImage')
    image.image = bpy.data.images.load(str(ENV / filename))
    links.new(uv.outputs['UV'], image.inputs['Vector'])
    if filename.endswith('normal.jpg'):
        image.image.colorspace_settings.name = 'Non-Color'
        normal = nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value = 1.3
        links.new(image.outputs['Color'], normal.inputs['Color'])
        links.new(normal.outputs['Normal'], bark_bsdf.inputs['Normal'])
    else:
        links.new(image.outputs['Color'], bark_bsdf.inputs['Base Color'])

verts, faces = [], []
segments, rings = 56, 25
for row in range(rings):
    z = row * .13 - .13
    for k in range(segments):
        angle = 2 * pi * k / segments
        radius = .303 + .10 * exp(-z * 4) + .017 * sin(5 * angle + z) + .012 * sin(13 * angle - z)
        verts.append((-.30 - .07 * z + radius * cos(angle),
                      .295 + .028 * z + .85 * radius * sin(angle), z))
for row in range(rings - 1):
    for k in range(segments):
        a, b = row * segments + k, row * segments + (k + 1) % segments
        faces.append((a, b, b + segments, a + segments))
trunk = mesh("Oak trunk", verts, faces, woodland, [bark])
uv_layer = trunk.data.uv_layers.new()
for face in trunk.data.polygons:
    row, k = divmod(face.index, segments)
    for index, (u, v) in zip(face.loop_indices, [(k, row), (k+1, row), (k+1, row+1), (k, row+1)]):
        uv_layer.data[index].uv = (2 * u / segments, v * .16)
    face.use_smooth = True

earth, earth_bsdf = surface("Meadow floor", (.14, .16, .051), .98)
nodes, links = earth.node_tree.nodes, earth.node_tree.links
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 2.2
tex = nodes.new('ShaderNodeTexCoord')
links.new(tex.outputs['Object'], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .19
ramp.color_ramp.elements[0].color = (.072, .089, .026, 1)
ramp.color_ramp.elements[1].position = .79
ramp.color_ramp.elements[1].color = (.29, .255, .073, 1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
links.new(ramp.outputs[0], earth_bsdf.inputs['Base Color'])


def height(x, y):
    return .061 * sin(x * .8 + y * .45) + .087 * sin(y * .66) + .025 * cos(2 * x - y)


verts, faces = [], []
for j in range(61):
    for i in range(61):
        x, y = (i - 30) * .64, (j - 8) * .64
        verts.append((x, y, height(x, y)))
for j in range(60):
    for i in range(60):
        a = j * 61 + i
        faces.append((a, a+1, a+62, a+61))
ground = mesh("Rolling field", verts, faces, woodland, [earth])
for face in ground.data.polygons:
    face.use_smooth = True

# Stems from the same patch share a traveling gust, with blade tips free to bend.
grass_mats = [surface("Field | " + name, color, .83)[0] for name, color in [
    ("moss", (.14, .20, .036)), ("olive", (.28, .29, .067)),
    ("rye", (.45, .32, .092)), ("sage", (.22, .31, .087)),
    ("pale seed", (.50, .38, .15)),
]]
meadow = collection("Meadow | wind ripple")
for patch in range(24):
    verts, faces, slots, offsets = [], [], [], []
    center_y = .45 + .37 * patch
    for blade in range(270):
        y = center_y + rng.uniform(-.24, .24)
        x = rng.uniform(-6.8, 4.7) - .30 * y
        h = rng.uniform(.13, .64) * (1 + .035 * y)
        angle = rng.uniform(0, 2*pi)
        dx, dy = cos(angle), sin(angle)
        width = rng.uniform(.006, .021)
        bend = rng.uniform(.035, .31)
        base = len(verts)
        for t in (0, .39, .73, 1):
            for edge in (-1, 1):
                w = width * (1 - t * .995) * edge
                verts.append((x + dx*bend*t*t - dy*w, y + dy*bend*t*t + dx*w, height(x, y) + h*t))
                offsets.append((h*t*t, x))
        slot = rng.randrange(4)
        for k in (0, 2, 4):
            faces.append((base+k, base+k+1, base+k+3, base+k+2))
            slots.append(slot)
        if blade % 8 == 0:
            tip = Vector(verts[-1])
            w = .015
            seed = len(verts)
            verts.extend([tip + Vector(v) for v in [(0,0,0), (w*dy,-w*dx,.057),
                                                    (0,0,.103),(-w*dy,w*dx,.045)]])
            offsets.extend([(h, x)] * 4)
            faces.append((seed, seed+1, seed+2, seed+3))
            slots.append(4)
    plants = mesh(f"Meadow patch {patch + 1:02}", verts, faces, meadow, grass_mats)
    for face, slot in zip(plants.data.polygons, slots):
        face.material_index = slot
    plants.shape_key_add(name="Calm")
    for direction in (-1, 1):
        bend_key = plants.shape_key_add(name="Downwind" if direction == 1 else "Recoil")
        for vert, (tip, x), original in zip(bend_key.data, offsets, verts):
            var = .82 + .18 * sin(x * 3.2)
            vert.co = (original[0] + direction*.48*tip*var,
                       original[1] + direction*.21*tip*var, original[2] - .09*tip)
        for frame in range(1, 49, 2):
            t = (frame-1)/12 - patch*.019
            gust = exp(-((t-1.9)/.61)**2) * sin((t-1.12)*8)
            bend_key.value = max(0, direction*gust) + .022 * (1 + sin(t*3 + patch))
            bend_key.keyframe_insert(data_path='value', frame=frame)

world = bpy.data.worlds.new("Late afternoon | autumn meadow")
scene.world = world
world.use_nodes = True
nodes, links = world.node_tree.nodes, world.node_tree.links
sky = nodes.new('ShaderNodeTexEnvironment')
sky.image = bpy.data.images.load(str(ENV / 'autumn_meadow_1k.hdr'))
links.new(sky.outputs[0], nodes.get('Background').inputs[0])
nodes.get('Background').inputs['Strength'].default_value = .45

lighting = collection("Late afternoon")
def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def light(name, kind, point, target, color, energy, size):
    data = bpy.data.lights.new(name, kind)
    data.color, data.energy = color, energy
    obj = bpy.data.objects.new(name, data)
    lighting.objects.link(obj)
    obj.location = point
    aim(obj, target)
    if kind == 'AREA':
        data.shape = 'DISK'
        data.size = size
    else:
        data.angle = size
    return obj


light("Low sun", 'SUN', (3.4, 4, 2.8), (0, 0, 1), (1, .71, .39), 2.15, .11)
light("Open sky on face", 'AREA', (.18, -.94, 1.51), (0, 0, 1.10), (.78, .87, 1), 26, .95)
light("Field bounce", 'AREA', (1.1, -.21, .88), (0, 0, 1.08), (1, .85, .62), 13, 1.4)

camera_data = bpy.data.cameras.new("Portrait lens")
camera = bpy.data.objects.new("Held three-quarter", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera.location = (.34, -.975, 1.105)
aim(camera, (.057, -.068, 1.095))
camera_data.lens = 57
camera_data.dof.use_dof = True
camera_data.dof.focus_distance = (camera.location - Vector((.015, -.127, 1.11))).length
camera_data.dof.aperture_fstop = 5.6

leaves = collection("Oak leaves | falling")
leaf_mats = [surface("Leaf | " + name, col, .54)[0] for name, col in [
    ("copper", (.49,.17,.025)), ("amber", (.60,.31,.05)),
    ("russet", (.31,.075,.022)), ("olive", (.25,.27,.052)),
    ("vein", (.29,.14,.045)),
]]
# A cupped blade with alternating lobes and a raised central rib.
profile = [(-.55,.014),(-.38,.11),(-.26,.25),(-.15,.144),(-.045,.30),
           (.055,.17),(.17,.285),(.24,.15),(.34,.19),(.50,.001)]
verts = []
for y, width in profile:
    verts.extend([(-width, y, .11*width + .10*y*y),
                  (0, y, .10*y*y - .024),
                  (width*.88, y, .20*width + .10*y*y)])
faces = []
for i in range(len(profile)-1):
    a = i*3
    faces.extend([(a,a+3,a+4,a+1), (a+1,a+4,a+5,a+2)])
rib_index = len(verts)
for y, width in [(-.68,.012),(-.48,.010),(-.19,.007),(.13,.005),(.43,.002)]:
    verts.extend([(-width,y,.10*y*y-.021),(width,y,.10*y*y-.021)])
faces.extend([(i,i+1,i+3,i+2) for i in range(rib_index,len(verts)-2,2)])
view_right, view_up, view_back = camera.rotation_euler.to_matrix().col
half_width = tan(camera_data.angle_x / 2)
half_height = half_width * 360 / 640
for i in range(13):
    leaf = mesh("Tracked oak leaf" if i == 0 else f"Falling oak leaf {i:02}", verts, faces, leaves, leaf_mats)
    for f in leaf.data.polygons:
        f.material_index = i % 4 if f.index < 18 else 4
        f.use_smooth = True
    size = .078 if i == 0 else rng.uniform(.046,.098)
    leaf.scale = (size, size, size)
    if i == 0:
        x, y, z, speed, entry, phase = .16, -.22, 1.234, .115, 1.04, .24
    else:
        depth = rng.uniform(1.10, 3.25)
        side = rng.uniform(-.63, .87)
        start = (camera.location - depth * view_back
                 + side * depth * half_width * view_right
                 + 1.10 * depth * half_height * view_up)
        x, y, z = start
        speed = 2 * half_height * depth * rng.uniform(.20, .49)
        entry, phase = rng.uniform(.87, 2.32), rng.uniform(0, 2*pi)
    for frame in range(1,49):
        t = (frame-1)/12 - entry
        drift = .050 * (1 + sin(t*2.8+phase)) + .035*t
        leaf.location = (x+drift, y+.035*sin(t*4+phase), z-speed*t+.016*cos(t*5+phase))
        leaf.rotation_euler = (1.12+.7*sin(t*4+phase), .65*cos(t*3.2+phase), phase+t*2.1)
        leaf.keyframe_insert(data_path='location', frame=frame)
        leaf.keyframe_insert(data_path='rotation_euler', frame=frame)

for frame, label in [(1,"Watch"), (13,"Breeze"), (32,"Settle"), (35,"Blink"), (48,"Hold")]:
    scene.timeline_markers.new(label, frame=frame)
for image in bpy.data.images:
    if not image.packed_file and image.source == 'FILE':
        path = Path(bpy.path.abspath(image.filepath))
        if path.is_file() and ASSETS in path.parents:
            image.pack()
            image.filepath = "//" + path.relative_to(ROOT).as_posix()
scene.frame_set(1)
