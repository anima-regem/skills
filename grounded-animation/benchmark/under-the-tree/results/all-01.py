"""Under the Tree. Build with Blender in background mode.

Face foundation adapted from Einar Rig, Blender Foundation, CC BY 4.0
https://studio.blender.org/characters/einar/v1/
https://creativecommons.org/licenses/by/4.0/
Oak bark and Autumn Meadow by Poly Haven, CC0, from the supplied assets.
"""
from math import cos, exp, sin, tau
from pathlib import Path
from random import Random

import bpy
from mathutils import Vector

assets = Path(__file__).resolve().parent / "assets"
env = assets / "environment"
rng = Random(29)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.eevee.taa_render_samples = 32
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'

with bpy.data.libraries.load(str(assets / 'einar.blend'), link=False) as (_, target):
    target.collections = ['CH-einar']
character = target.collections[0]
scene.collection.children.link(character)
rig = bpy.data.objects['RIG-einar']
rig.location.z -= .69
for obj in character.all_objects:
    if obj.parent is None and obj != rig and not obj.name.startswith('WGT'):
        obj.location.z -= .69
    if obj.name.startswith(('WGT', 'GEO-einar_hat', 'GEO-einar_beard.messy',
                            'GEO-einar_mustache.messy')):
        obj.hide_render = True
        obj.hide_set(True)
character.name = 'Rowan • field naturalist'


def material(name, color, roughness=.75):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return mat


def tint(mat_name, color, strength):
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        return
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    for shader in list(nodes):
        if shader.type != 'BSDF_PRINCIPLED':
            continue
        base = shader.inputs['Base Color']
        if base.is_linked:
            mix = nodes.new('ShaderNodeMixRGB')
            mix.blend_type = 'MIX'
            mix.inputs[0].default_value = strength
            mix.inputs[2].default_value = (*color, 1)
            links.new(base.links[0].from_socket, mix.inputs[1])
            links.new(mix.outputs[0], base)
        else:
            old = tuple(base.default_value)
            base.default_value = (*(a*(1-strength)+b*strength for a,b in zip(old, color)), 1)


canvas = material('Rowan • weathered pine canvas', (.048, .091, .077), .83)
nodes, links = canvas.node_tree.nodes, canvas.node_tree.links
shader = nodes['Principled BSDF']
uv = nodes.new('ShaderNodeTexCoord')
weave = nodes.new('ShaderNodeVectorMath')
weave.operation = 'SCALE'
weave.inputs['Scale'].default_value = 10
links.new(uv.outputs['UV'], weave.inputs[0])
texture = nodes.new('ShaderNodeTexImage')
texture.image = bpy.data.images['canvas_01.normal']
links.new(weave.outputs[0], texture.inputs['Vector'])
normal = nodes.new('ShaderNodeNormalMap')
normal.inputs['Strength'].default_value = .29
links.new(texture.outputs[0], normal.inputs['Color'])
links.new(normal.outputs[0], shader.inputs['Normal'])
shader.inputs['Sheen Weight'].default_value = .18
bpy.data.objects['GEO-einar_jacket_main'].data.materials[0] = canvas
tint('einar.jacket.collar', (.078, .130, .115), .58)
tint('einar.jacket.rim', (.075, .105, .082), .60)
tint('einar.sweater', (.18, .090, .043), .60)
tint('eyes.iris', (.095, .131, .068), .32)


def pose(name, channel, keys):
    bone = rig.pose.bones[name]
    if channel == 'rotation_euler':
        bone.rotation_mode = 'XYZ'
    for frame, value in keys:
        setattr(bone, channel, value)
        bone.keyframe_insert(data_path=channel, frame=frame, group=name)


pose('FK-Head', 'rotation_euler', [
    (1, (-.018, .067, -.024)), (16, (-.016, .069, -.024)),
    (22, (-.021, .083, -.024)), (29, (-.038, .149, -.012)),
    (34, (-.061, .170, -.011)), (48, (-.073, .170, -.010)),
])
pose('MSTR-TGT-Eyes', 'location', [
    (1, (-.095, 0, .022)), (13, (-.095, 0, .023)),
    (16, (-.142, 0, .046)), (19, (-.248, 0, .015)),
    (24, (-.264, 0, -.028)), (31, (-.280, 0, -.128)),
    (36, (-.286, 0, -.175)), (43, (-.221, 0, -.132)),
    (48, (-.218, 0, -.130)),
])
pose('FK-Chest', 'rotation_euler', [
    (1, (.003, 0, -.007)), (12, (.009, 0, -.006)), (26, (.001, 0, -.007)),
    (39, (.008, 0, -.006)), (48, (.005, 0, -.006)),
])
pose('MSTR-Jaw', 'rotation_euler', [(1, (.005, 0, 0)), (33, (.005, 0, 0)),
                                   (40, (.019, 0, 0)), (48, (.017, 0, 0))])
for side, sign in [('L', 1), ('R', -1)]:
    pose('ACT-Eyebrow_Inner.' + side, 'location', [
        (1, (-sign*.0025, -.0038, .0003)), (22, (-sign*.0021, -.0024, .0003)),
        (33, (-sign*.002, -.0028, 0)), (41, (-sign*.0008, -.0007, 0)),
        (48, (-sign*.0008, -.0007, 0)),
    ])
    pose('Blink.' + side, 'location', [
        (1, (0, 0, 0)), (34, (0, 0, 0)), (35, (0, -.0035, 0)),
        (36, (0, -.0062, 0)), (37, (0, -.0024, 0)), (39, (0, 0, 0)),
        (48, (0, 0, 0)),
    ])
    pose('ACT-Mouth_Corner.' + side, 'location', [
        (1, (-.00125, -.0012, 0)), (32, (-.00125, -.0012, 0)),
        (39, (.0003, -.00035, 0)), (48, (.0002, -.00025, 0)),
    ])


def mesh(name, verts, faces, mat=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    if mat:
        data.materials.append(mat)
    return obj


def point(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


camera = bpy.data.objects.new('Held close-up', bpy.data.cameras.new('Portrait lens'))
scene.collection.objects.link(camera)
camera.location = (.323, -.970, 1.010)
point(camera, (.055, -.087, .975))
camera.data.lens = 54
camera.data.dof.use_dof = True
camera.data.dof.focus_distance = (camera.location - Vector((0, -.115, .975))).length
camera.data.dof.aperture_fstop = 8
scene.camera = camera

world = bpy.data.worlds.new('Late afternoon sky')
scene.world = world
world.use_nodes = True
nodes, links = world.node_tree.nodes, world.node_tree.links
sky = nodes.new('ShaderNodeTexEnvironment')
sky.image = bpy.data.images.load(str(env / 'autumn_meadow_1k.hdr'))
mapping = nodes.new('ShaderNodeMapping')
mapping.inputs['Rotation'].default_value.z = 1.70
coords = nodes.new('ShaderNodeTexCoord')
links.new(coords.outputs['Generated'], mapping.inputs['Vector'])
links.new(mapping.outputs['Vector'], sky.inputs['Vector'])
links.new(sky.outputs['Color'], nodes['Background'].inputs['Color'])
nodes['Background'].inputs['Strength'].default_value = .49


def light(name, position, target, energy, color, size):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.color, data.shape, data.size = energy, color, 'DISK', size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    point(obj, target)


light('Open sky through the canopy', (-.75, -.90, 1.95), (0, -.05, 1), 37, (.78, .87, 1), 1.22)
light('Field bounce', (1.55, -.55, .87), (0, 0, 1), 22, (1, .88, .72), 1.25)
light('Late sun on the tree edge', (.31, .56, 1.85), (0, 0, 1), 40, (1, .70, .40), .48)
sun_data = bpy.data.lights.new('Sun across the meadow', 'SUN')
sun_data.energy, sun_data.angle, sun_data.color = 1.35, .10, (1, .78, .49)
sun = bpy.data.objects.new(sun_data.name, sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (.53, -.81, -.45)

bark = material('Jolcham oak bark', (.19, .11, .057), .9)
nodes, links = bark.node_tree.nodes, bark.node_tree.links
base = nodes['Principled BSDF']
diffuse = nodes.new('ShaderNodeTexImage')
diffuse.image = bpy.data.images.load(str(env / 'oak_bark_diffuse.jpg'))
links.new(diffuse.outputs['Color'], base.inputs['Base Color'])
normal = nodes.new('ShaderNodeTexImage')
normal.image = bpy.data.images.load(str(env / 'oak_bark_normal.jpg'))
normal.image.colorspace_settings.name = 'Non-Color'
converter = nodes.new('ShaderNodeNormalMap')
converter.inputs['Strength'].default_value = .85
links.new(normal.outputs['Color'], converter.inputs['Color'])
links.new(converter.outputs[0], base.inputs['Normal'])


def trunk(name, centers, radii, around=72):
    verts, faces = [], []
    for ring, ((x, y, z), radius) in enumerate(zip(centers, radii)):
        for j in range(around):
            angle = tau*j/around
            ridge = 1 + .055*sin(9*angle+z*.9) + .04*sin(16*angle-z*2) + .025*sin(29*angle+z)
            verts.append((x+radius*ridge*cos(angle), y+radius*ridge*sin(angle), z))
            if ring:
                a = (ring-1)*around + j
                b = (ring-1)*around + (j+1)%around
                faces.append((a, b, b+around, a+around))
    obj = mesh(name, verts, faces, bark)
    uv = obj.data.uv_layers.new()
    for p in obj.data.polygons:
        ring, j = divmod(p.index, around)
        u0, u1 = 3.0*j/around, 3.0*(j+1)/around
        v0, v1 = centers[ring][2]*1.9, centers[ring+1][2]*1.9
        for i, coord in zip(p.loop_indices, ((u0,v0),(u1,v0),(u1,v1),(u0,v1))):
            uv.data[i].uv = coord
        p.use_smooth = True


centers, radii = [], []
for i in range(37):
    z = -.16 + .12*i
    centers.append((-.285-.053*z+.021*sin(z*2), .286+.024*sin(z*2.6), z))
    radii.append(.33-.028*z+.145*exp(-max(0,z)*7))
trunk('Oak • shoulder contact', centers, radii)
trunk('Oak • rising bough', [(-.36-.17*i, .28+.057*i, 1.52+.18*i)
                            for i in range(15)], [.20-.011*i for i in range(15)], 40)

ground = material('Dry meadow soil', (.135, .146, .041))
nodes, links = ground.node_tree.nodes, ground.node_tree.links
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.6
noise.inputs['Detail'].default_value = 4
coordinates = nodes.new('ShaderNodeTexCoord')
links.new(coordinates.outputs['Object'], noise.inputs[0])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .17
ramp.color_ramp.elements[0].color = (.047, .061, .019, 1)
ramp.color_ramp.elements[1].position = .8
ramp.color_ramp.elements[1].color = (.27, .24, .081, 1)
links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
links.new(ramp.outputs[0], nodes['Principled BSDF'].inputs['Base Color'])


def elevation(x, y):
    return .085*sin(y*.44) + .09*sin(.47*x+.17*y)*sin(.36*y) + .015*y


verts = [(float(x), float(y), elevation(x, y)) for y in range(-3, 57) for x in range(-32, 33)]
faces = [(i,i+1,i+66,i+65) for i in range(len(verts)-65) if i % 65 != 64]
terrain = mesh('Meadow slope', verts, faces, ground)
for poly in terrain.data.polygons:
    poly.use_smooth = True

grass_mats = [material('Meadow blade %s' % i, color) for i, color in enumerate([
    (.13,.19,.052), (.225,.27,.075), (.34,.33,.105), (.38,.28,.075),
    (.085,.132,.04), (.46,.39,.18), (.18,.214,.077),
])]

# Blades bend from rooted bases. The gust travels from the oak side across the meadow.
for band in range(9):
    verts, faces, indices, bend = [], [], [], []
    center_x = -.8 + band*.49
    for i in range(390):
        x = center_x + rng.uniform(-.27,.27)
        y = rng.uniform(.23, 9.2)
        if y < .61 and x < .20:
            continue
        z = elevation(x,y)
        h = rng.uniform(.095,.50) * (1.12 if y < 2.8 else .88)
        w = rng.uniform(.005,.019)
        angle = rng.uniform(0,tau)
        dx, dy = cos(angle), sin(angle)
        lean = rng.uniform(.09,.6)*h
        j = len(verts)
        for t in (0,.43,.78,1):
            width = w*(1-t*.94)
            verts.extend([(x+dx*lean*t*t-sign*dy*width, y+dy*lean*t*t+sign*dx*width,
                           z+t*h) for sign in (-1,1)])
            bend.extend([t*t*h]*2)
        faces.extend([(j+k,j+k+1,j+k+3,j+k+2) for k in (0,2,4)])
        indices.extend([rng.randrange(len(grass_mats))]*3)
    obj = mesh('Wind lane %02d' % band, verts, faces)
    for mat in grass_mats:
        obj.data.materials.append(mat)
    for poly, index in zip(obj.data.polygons, indices):
        poly.material_index = index
    obj.shape_key_add(name='Rooted meadow')
    gust = obj.shape_key_add(name='Blade flex')
    for vertex, amount in zip(gust.data, bend):
        vertex.co.x += .63*amount
        vertex.co.y += .21*amount
        vertex.co.z -= .13*amount
    delay = band*.78
    for frame in range(1,49):
        phase = frame-14-delay
        envelope = exp(-((phase-5)/7.5)**2) if phase > -9 else 0
        gust.value = .06 + envelope*(.64+.31*cos(.58*(phase-4))) + .025*sin(.32*frame+band)
        gust.keyframe_insert(data_path='value', frame=frame)

leaf_mats = [material('Fallen oak • '+name, color, .57) for name,color in [
    ('ochre', (.54,.235,.035)), ('russet', (.38,.095,.022)),
    ('gold', (.66,.34,.066)), ('olive', (.23,.25,.055)),
]]
vein = material('Leaf veins', (.245,.116,.023))
outline = [(-.48,0),(-.36,.14),(-.28,.26),(-.13,.22),(-.05,.39),(.08,.33),
           (.20,.43),(.28,.29),(.40,.31),(.52,0),(.38,-.28),(.27,-.25),
           (.17,-.41),(.045,-.31),(-.065,-.34),(-.16,-.22),(-.28,-.25),(-.36,-.13)]
scene.frame_set(1)
bpy.context.view_layer.update()
orientation = camera.rotation_euler.to_matrix()
right, up, forward = [orientation @ Vector(v) for v in [(1,0,0),(0,1,0),(0,0,-1)]]


def leaf(name, length, mat):
    verts = [(0,0,.11*length)] + [(u*length,v*length,(.035*sin(9*u)+.18*u)*length)
                                  for u,v in outline]
    faces = [(0,i+1,(i+1)%len(outline)+1) for i in range(len(outline))]
    k = len(verts)
    verts.extend([(-.53*length,-.013*length,.002),(-.53*length,.013*length,.002),
                  (0,.009*length,.113*length),(0,-.009*length,.113*length),
                  (.47*length,.003*length,.089*length)])
    faces.extend([(k,k+3,k+2,k+1),(k+3,k+4,k+2)])
    obj = mesh(name, verts, faces, mat)
    obj.data.materials.append(vein)
    for p in list(obj.data.polygons)[-2:]:
        p.material_index = 1
    return obj


# Flutter is keyed at the delivery rate. The featured leaf follows the open field side.
for i, (release, x, y, depth, fall, size) in enumerate([
    (13,.079,.116,.55,.057,.028), (10,.255,.251,1.24,.104,.043),
    (16,.53,.30,1.64,.153,.053), (21,.255,.29,1.46,.095,.055),
    (27,.416,.22,1.17,.079,.032), (18,-.47,.24,1.31,.151,.043),
    (30,.310,.33,1.55,.142,.046),
]):
    obj = leaf('Falling oak leaf %02d' % (i+1), size, leaf_mats[i%4])
    obj.rotation_mode = 'XYZ'
    for frame in range(1,49):
        t = (frame-release)/12
        u = max(0,t)
        drift_scale = .59 if i == 0 else 1
        x_drift = drift_scale*(.039*u + .017*sin(5.8*u+i)*min(1,u*5))
        vertical = y-fall*u + drift_scale*(-.012*(1-exp(-5*u))+.007*sin(7*u+i)*min(1,u*4))
        obj.location = (camera.location + right*(x+x_drift) + up*vertical
                        + forward*(depth+.030*drift_scale*sin(3.6*u+i)))
        obj.rotation_euler = (1.03+.69*sin(6.3*u+i), .49*sin(8*u+i), i*1.23+1.7*u)
        obj.keyframe_insert(data_path='location', frame=frame)
        obj.keyframe_insert(data_path='rotation_euler', frame=frame)

scene['Asset credit'] = 'Einar Rig adapted from Blender Foundation, CC BY 4.0. Poly Haven environment maps, CC0.'
scene.frame_set(1)
assert scene.camera and (scene.frame_end-scene.frame_start+1)/scene.render.fps == 4
