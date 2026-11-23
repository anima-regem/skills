"""Build Under the Tree from Blender factory startup."""
from pathlib import Path
from math import sin, cos, tau, exp
import random

import bpy
from mathutils import Vector

ASSETS = Path(__file__).resolve().parent / "assets"
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'
rng = random.Random(72)


def mesh(name, vertices, faces, materials, indices=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    for material in materials:
        data.materials.append(material)
    if indices is not None:
        for polygon, index in zip(data.polygons, indices):
            polygon.material_index = index
    return obj


def surface(name, color, roughness=.75):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat, bsdf


def noise_color(mat, bsdf, scale, colors):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    coord = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = scale
    ramp = nodes.new('ShaderNodeValToRGB')
    for element, position, color in zip(ramp.color_ramp.elements, (.22, .78), colors):
        element.position = position
        element.color = (*color, 1)
    links.new(coord.outputs['Object'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], ramp.inputs[0])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])


# The supplied production rig provides the facial deformation and groom.
with bpy.data.libraries.load(str(ASSETS / 'einar.blend'), link=False) as (_, dst):
    dst.collections = ['CH-einar']
character = dst.collections[0]
scene.collection.children.link(character)
character.name = 'Rowan | head and shoulders'
rig = bpy.data.objects['RIG-einar']
rig.animation_data_clear()
rig.location.z -= .57
for name in ('hair', 'beard', 'mustache'):
    bpy.data.objects['GEO-einar_' + name + '.messy'].hide_render = True

# Keep the rig's expression deltas while changing the neutral cheek and nose
# profile. The same vertex offset is applied to every facial shape.
head = bpy.data.objects['GEO-einar_head']
shapes = head.data.shape_keys.key_blocks
# Drive both lid masks on each eye from its blink control.
drivers = head.data.shape_keys.animation_data.drivers
for side in ('L', 'R'):
    for lid in ('Upper', 'Lower'):
        driver = drivers.find(shapes[f'D_Blink_{lid}.{side}'].path_from_id('value')).driver
        driver.variables[0].targets[0].bone_target = 'Blink.' + side

for i, point in enumerate(shapes[0].data):
    x, y, z = point.co
    cheek = exp(-((abs(x)-.074)/.036)**2 - ((z-1.574)/.041)**2 - ((y+.093)/.056)**2)
    bridge = exp(-(x/.024)**2 - ((z-1.601)/.029)**2 - ((y+.142)/.041)**2)
    offset = Vector((.007*cheek*x/.074, -.008*bridge + .003*cheek, -.004*bridge))
    for shape in shapes:
        shape.data[i].co += offset

hair_ramp = bpy.data.materials['einar.hair'].node_tree.nodes['ColorRamp.001'].color_ramp
for element, color in zip(hair_ramp.elements,
                          ((.029,.016,.011), (.13,.078,.047), (.27,.20,.146),
                           (.56,.53,.45), (.89,.88,.81))):
    element.color = (*color, 1)

hat = bpy.data.objects['GEO-einar_hat']
hat.hide_render = False
knit, knit_bsdf = surface('Rowan | charcoal wool', (.052, .065, .073), .91)
noise_color(knit, knit_bsdf, 185, ((.023,.031,.038), (.085,.103,.112)))
for i in range(len(hat.data.materials)):
    hat.data.materials[i] = knit

canvas, canvas_bsdf = surface('Rowan | evergreen canvas', (.038, .081, .070))
noise_color(canvas, canvas_bsdf, 95, ((.021, .043, .039), (.067, .116, .093)))
jacket = bpy.data.objects['GEO-einar_jacket_main']
for i, mat in enumerate(jacket.data.materials):
    if mat and mat.name == 'einar.jacket.canvas':
        jacket.data.materials[i] = canvas

credits = bpy.data.texts.new('Asset credits')
credits.write('Facial rig, base mesh and groom adapted from Einar Rig, Blender Foundation, CC BY 4.0.\n'
              'https://studio.blender.org/characters/einar/v1/\n'
              'Jolcham Oak Bark, Charlotte Baglioni, Poly Haven, CC0.\n'
              'Autumn Meadow, Sergej Majboroda, Poly Haven, CC0.\n')


def pose(name, channel, values):
    bone = rig.pose.bones[name]
    for frame, value in values:
        setattr(bone, channel, value)
        bone.keyframe_insert(channel, frame=frame, group=name)


pose('MSTR-TGT-Eyes', 'location', [
    (1, (-.056, 0, .018)), (15, (-.056, 0, .018)), (18, (-.28, 0, .035)),
    (20, (-.32, 0, .008)), (27, (-.36, 0, -.082)), (33, (-.37, 0, -.186)),
    (41, (-.33, 0, -.211)), (48, (-.33, 0, -.211)),
])
pose('FK-Head', 'rotation_euler', [
    (1, (.022, -.065, -.026)), (19, (.022, -.065, -.026)),
    (23, (.011, .006, -.021)), (31, (.041, .057, -.01)),
    (41, (.088, .054, -.008)), (48, (.088, .054, -.008)),
])
pose('MSTR-Spine_Torso', 'location', [
    (1, (0, 0, 0)), (14, (0, .0018, 0)), (28, (0, -.0008, 0)),
    (45, (0, .0012, 0)), (48, (0, .001, 0)),
])
for side in ('L', 'R'):
    asymmetry = 1 if side == 'L' else .78
    pose('ACT-Eyebrow_Inner.' + side, 'location', [
        (1, (0, -.0024 * asymmetry, 0)), (13, (0, -.0024 * asymmetry, 0)),
        (20, (0, -.0010 * asymmetry, 0)), (29, (0, -.0019 * asymmetry, 0)),
        (42, (0, -.0011 * asymmetry, 0)),
    ])
    pose('ACT-Mouth_Corner.' + side, 'location', [
        (1, (-.00145 * asymmetry, 0, 0)), (32, (-.00145 * asymmetry, 0, 0)),
        (41, (.00045 * asymmetry, 0, 0)), (48, (.00045 * asymmetry, 0, 0)),
    ])
    pose('Blink.' + side, 'location', [
        (1, (0, 0, 0)), (34, (0, 0, 0)), (35, (0, -.006, 0)),
        (36, (0, -.003, 0)), (38, (0, 0, 0)), (48, (0, 0, 0)),
    ])

camera_data = bpy.data.cameras.new('Portrait 63 mm')
camera = bpy.data.objects.new('Locked portrait', camera_data)
scene.collection.objects.link(camera)
camera.location = (.337, -.828, 1.102)
camera.rotation_euler = (Vector((.065, -.08, 1.068)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera_data.lens = 63
camera_data.dof.use_dof = True
camera_data.dof.focus_distance = .797
camera_data.dof.aperture_fstop = 6.3
scene.camera = camera

bark, bark_bsdf = surface('Oak | ridged bark', (.13, .073, .037))
nodes, links = bark.node_tree.nodes, bark.node_tree.links
normal = nodes.new('ShaderNodeNormalMap')
normal.inputs['Strength'].default_value = .89
for filename, destination in (
    ('oak_bark_diffuse.jpg', bark_bsdf.inputs['Base Color']),
    ('oak_bark_normal.jpg', normal.inputs['Color']),
):
    img = bpy.data.images.load(str(ASSETS / 'environment' / filename), check_existing=True)
    if destination == normal.inputs['Color']:
        img.colorspace_settings.name = 'Non-Color'
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = img
    links.new(tex.outputs['Color'], destination)
links.new(normal.outputs['Normal'], bark_bsdf.inputs['Normal'])

verts, faces = [], []
segments, rings = 96, 65
for j in range(rings):
    z = -.18 + j * .063
    for i in range(segments):
        a = tau * i / segments
        radius = (.303 + .09 * exp(-max(0, z)*7)
                  + .014*sin(7*a + .9*z) + .008*sin(17*a - 2*z)
                  + .008*sin(29*a + sin(2*z)) + .003*sin(45*a - 4*z))
        verts.append((-.239 - .047*z + radius*cos(a), .297 + .018*sin(z*2) + radius*sin(a), z))
        if j:
            k = (j-1)*segments + i
            l = (j-1)*segments + (i+1) % segments
            faces.append((k, l, l+segments, k+segments))
trunk = mesh('Oak | leaning trunk', verts, faces, [bark])
uv = trunk.data.uv_layers.new()
for poly in trunk.data.polygons:
    poly.use_smooth = True
    j, i = divmod(poly.index, segments)
    for loop, (u, v) in zip(poly.loop_indices, ((i, j), (i+1, j), (i+1, j+1), (i, j+1))):
        uv.data[loop].uv = (3*u/segments, v*.083)

ground, ground_bsdf = surface('Meadow | moss and dry grass', (.22, .23, .078))
noise_color(ground, ground_bsdf, 1.9, ((.084, .113, .029), (.33, .29, .095)))


def elevation(x, y):
    return -.04 + .11*sin(.8*x+.2)*sin(.54*y) + .14*sin(.33*y)*min(1, y/3)


verts, faces = [], []
for j in range(65):
    for i in range(81):
        x, y = -25 + i*.65, -4 + j*.55
        verts.append((x, y, elevation(x, y)))
        if i and j:
            k = j*81 + i
            faces.append((k-82, k-81, k, k-1))
terrain = mesh('Rolling meadow', verts, faces, [ground])
for poly in terrain.data.polygons:
    poly.use_smooth = True

grass = []
for i, color in enumerate(((.11,.18,.037), (.19,.26,.060), (.27,.29,.073),
                            (.37,.33,.106), (.33,.40,.087), (.46,.38,.157))):
    mat, shader = surface('Meadow blade %d' % i, color)
    shader.inputs['Emission Color'].default_value = (*color, 1)
    shader.inputs['Emission Strength'].default_value = .085
    grass.append(mat)

# Paired bend shapes keep the blade roots fixed. The gust crosses successive
# strips of the meadow with a delay and each strip has its own flutter phase.
for band in range(17):
    verts, faces, indices, weights = [], [], [], []
    for tuft in range(230):
        x = -4.8 + band*.48 + rng.random()*.48
        y = rng.uniform(.55, 10.5)
        h = rng.uniform(.09, .28)
        if tuft % 11 == 0:
            h *= 1.7
        for blade in range(5):
            angle = rng.uniform(0, tau)
            dx, dy = cos(angle), sin(angle)
            bx, by = x + rng.uniform(-.055,.055), y + rng.uniform(-.055,.055)
            z = elevation(bx, by)
            length = h*rng.uniform(.46,1.24)
            lean = length*rng.uniform(.17,.59)
            width = rng.uniform(.003,.012)
            start = len(verts)
            index = rng.randrange(len(grass))
            for t in (0, .34, .69, 1):
                for sign in (-1, 1):
                    w = sign*width*(1-t*.98)
                    verts.append((bx + dx*lean*t*t - dy*w, by + dy*lean*t*t + dx*w,
                                  z + length*t*(1-.18*t*t)))
                    weights.append(length*t*t)
            for step in (0, 2, 4):
                k = start+step
                faces.append((k,k+1,k+3,k+2))
                indices.append(index)
    patch = mesh('Meadow wind strip %02d' % band, verts, faces, grass, indices)
    patch.shape_key_add(name='Still')
    bend = patch.shape_key_add(name='Gust')
    bend.slider_min = -1
    for point, weight in zip(bend.data, weights):
        point.co.x += weight*.68
        point.co.y += weight*.25
        point.co.z -= weight*.17
    for f in range(1, 49, 2):
        arrival = (f-1)/12 - (band-8)*.071
        envelope = exp(-((arrival-1.82)/.66)**2)
        bend.value = .052*sin(f*.33-band*.57) + envelope*(.58+.32*sin(8*arrival))
        bend.keyframe_insert('value', frame=f)

world = bpy.data.worlds.new('Late afternoon meadow')
world.use_nodes = True
scene.world = world
wn, wl = world.node_tree.nodes, world.node_tree.links
sky = wn.new('ShaderNodeTexEnvironment')
sky.image = bpy.data.images.load(str(ASSETS / 'environment' / 'autumn_meadow_1k.hdr'), check_existing=True)
bg = wn.get('Background')
wl.new(sky.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = .48


def light(name, kind, location, target, color, power, size):
    data = bpy.data.lights.new(name, kind)
    data.energy, data.color = power, color
    if kind == 'AREA':
        data.shape, data.size = 'DISK', size
    else:
        data.angle = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


light('Low afternoon sun', 'SUN', (-4, 5, 3.0), (0, 0, 0), (1, .77, .50), 2.05, .09)
light('Open sky | portrait fill', 'AREA', (-.73, -1.28, 2.0), (0, -.1, 1.06), (.77, .87, 1), 40, 1.45)
light('Meadow bounce', 'AREA', (1.1, -.38, .72), (0, -.1, 1.08), (1, .83, .61), 12, 1.1)
light('Sun through canopy', 'AREA', (.23, .74, 2.15), (0, -.01, 1.1), (1, .69, .38), 39, .58)


def make_leaf(name, length, color):
    material, shader = surface(name + ' | lamina', color, .53)
    shader.inputs['Subsurface Weight'].default_value = .085
    noise_color(material, shader, 125, (tuple(c*.57 for c in color), tuple(c*1.23 for c in color)))
    vein, _ = surface(name + ' | veins', tuple(c*.69 for c in color))
    outline = [(0,-.55),(.16,-.33),(.29,-.25),(.22,-.15),(.38,-.056),(.27,.03),
               (.31,.16),(.21,.22),(.24,.31),(.12,.36),(0,.55)]
    outline += [(-x*.89,y+.015) for x,y in outline[-2:0:-1]]
    vertices = [(0, 0, .072*length)]
    vertices += [(x*length,y*length,(.038*sin(y*5)-.085*abs(x))*length) for x,y in outline]
    faces = [(0,i+1,(i+1)%len(outline)+1) for i in range(len(outline))]
    indices = [0]*len(faces)
    for start_y, end_x, end_y, width in [(-.61,0,.48,.012),(-.3,.22,-.14,.007),
                                         (-.25,-.24,-.10,.006),(-.10,.25,.09,.006),
                                         (-.04,-.23,.17,.006),(.12,.15,.30,.005)]:
        i = len(vertices)
        vertices.extend((x*length, y*length, z*length) for x,y,z in
                        ((-width,start_y,.078),(width,start_y,.078),(end_x,end_y,.069)))
        faces.append((i,i+1,i+2))
        indices.append(1)
    return mesh(name, vertices, faces, [material,vein], indices)


# Place the falling leaves using the fixed camera's image plane. The tracked
# leaf travels in open space beside the portrait, outside the facial silhouette.
bpy.context.view_layer.update()
camera_basis = camera.matrix_world.to_quaternion()
leaf_specs = [
    ('Copper leaf | gaze cue', .044, (.52,.205,.037), 12, 2.24, .79, .073, .063),
    ('Gold leaf', .043, (.58,.32,.055), 10, 2.91, .61, .133, .052),
    ('Russet leaf', .061, (.32,.129,.036), 15, 3.30, .86, .123, .079),
    ('Ochre leaf', .058, (.64,.36,.053), 18, 3.70, .94, .156, .069),
    ('Umber leaf', .033, (.34,.16,.048), 23, 3.52, .58, .153, .108),
    ('Distant leaf', .051, (.60,.29,.036), 27, 3.74, .74, .150, .066),
]
for i, (name, size, color, first, duration, depth, x0, drift) in enumerate(leaf_specs):
    leaf = make_leaf(name, size, color)
    for f in range(1, 49):
        t = ((f-first)/12)/duration
        horizontal = x0 + drift*t + (.010 if i == 0 else .018)*sin(9*t+i)
        vertical = (.159 if i == 0 else .181) - .44*t + .018*sin(7*t+i)
        coords = Vector((horizontal*depth, vertical*depth, -depth-.044*sin(t*5+i)))
        leaf.location = camera.location + camera_basis @ coords
        leaf.rotation_euler = (camera_basis @ Vector((0,0,1)).rotation_difference(
            Vector((.59*sin(t*10+i), .6*cos(t*7+i), .83)))).to_euler()
        leaf.rotation_euler.rotate_axis('Z', -.48 + .95*sin(8*t+i))
        leaf.keyframe_insert('location', frame=f)
        leaf.keyframe_insert('rotation_euler', frame=f)

for name, frame in [('Watching', 1), ('Breeze', 13), ('Settling', 32), ('Hold', 42)]:
    scene.timeline_markers.new(name, frame=frame)
bpy.ops.file.pack_all()
scene.frame_set(1)
