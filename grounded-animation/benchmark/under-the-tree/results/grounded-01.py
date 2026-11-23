"""Under the Tree. Execute with Blender in background mode."""
import bpy
from mathutils import Vector
from math import sin, cos, pi, exp
from pathlib import Path
from random import Random

assets = Path(__file__).resolve().parent / "assets"
rng = Random(37)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'

def material(name, color, roughness=.65):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    return m

def mesh(name, vertices, faces, mat=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    if mat:
        data.materials.append(mat)
    return obj

def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

with bpy.data.libraries.load(str(assets / 'einar.blend'), link=False) as (_, lib):
    lib.collections = ['CH-einar']
character = lib.collections[0]
scene.collection.children.link(character)
rig = bpy.data.objects['RIG-einar']
if rig.animation_data:
    rig.animation_data.action = None
for obj in list(character.all_objects):
    if obj.parent is None and not obj.name.startswith('WGT-'):
        obj.location.z -= .70
    if obj.name.startswith('WGT-') or obj.name.endswith('.messy') or obj.name in {
        'GEO-einar_hat', 'GEO-einar_head.base.001', 'GEO-einar_mustache_surfdef2'
    }:
        # Surface deformation proxies still evaluate for the attached groom.
        obj.driver_remove('hide_render')
        obj.hide_render = True
    if obj.name == 'GEO-einar_hat':
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)

# Rowan uses the supplied Blender Foundation Einar rig (CC BY 4.0),
# with a custom costume palette, exposed hair and reshaped facial proportions.
# https://studio.blender.org/characters/einar/v1/
canvas = material('Rowan waxed slate canvas', (.085,.155,.167), .78)
nodes, links = canvas.node_tree.nodes, canvas.node_tree.links
shader = nodes.get('Principled BSDF')
shader.inputs['Sheen Weight'].default_value = .16
coordinates = nodes.new('ShaderNodeTexCoord')
weave = nodes.new('ShaderNodeTexNoise')
weave.inputs['Scale'].default_value = 950
weave.inputs['Detail'].default_value = 2.5
links.new(coordinates.outputs['Object'], weave.inputs['Vector'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .32
bump.inputs['Distance'].default_value = .00045
links.new(weave.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs['Normal'], shader.inputs['Normal'])
mottle = nodes.new('ShaderNodeTexNoise')
mottle.inputs['Scale'].default_value = 42
links.new(coordinates.outputs['Object'], mottle.inputs['Vector'])
dye = nodes.new('ShaderNodeValToRGB')
dye.color_ramp.elements[0].color = (.023,.061,.069,1)
dye.color_ramp.elements[1].color = (.138,.225,.229,1)
links.new(mottle.outputs['Fac'], dye.inputs[0])
links.new(dye.outputs[0], shader.inputs['Base Color'])
jacket = bpy.data.objects['GEO-einar_jacket_main']
jacket.data.materials[0] = canvas


groom = material('Rowan dark brown groom', (.052,.027,.016), .76)
nodes, links = groom.node_tree.nodes, groom.node_tree.links
shader = nodes.get('Principled BSDF')
shader.inputs['Specular IOR Level'].default_value = .23
strand = nodes.new('ShaderNodeHairInfo')
pigment = nodes.new('ShaderNodeValToRGB')
pigment.color_ramp.elements[0].color = (.016,.009,.006,1)
pigment.color_ramp.elements[1].color = (.135,.079,.043,1)
links.new(strand.outputs['Random'], pigment.inputs[0])
links.new(pigment.outputs[0], shader.inputs['Base Color'])
for obj in character.all_objects:
    if obj.type == 'CURVES':
        for i, mat in enumerate(obj.data.materials):
            if mat and mat.name == 'einar.hair':
                obj.data.materials[i] = groom

for name, tint in [('einar.jacket.rim', (.25,.47,.56)),
                   ('einar.jacket.collar', (.23,.46,.51)),
                   ('einar.sweater', (.63,.40,.26)),
                   ('einar.skin', (.84,.89,.96)),
                   ('eyes.iris', (.83,.98,.72))]:
    mat = bpy.data.materials.get(name)
    if not mat or not mat.use_nodes:
        continue
    tree = mat.node_tree
    for shader in list(tree.nodes):
        if shader.type != 'BSDF_PRINCIPLED':
            continue
        base = shader.inputs['Base Color']
        if base.is_linked:
            source = base.links[0].from_socket
            mult = tree.nodes.new('ShaderNodeMixRGB')
            mult.blend_type = 'MULTIPLY'
            mult.inputs[0].default_value = 1
            mult.inputs[2].default_value = (*tint, 1)
            tree.links.new(source, mult.inputs[1])
            tree.links.new(mult.outputs[0], base)

# Subtle changes in cheekbone and jaw width, preserving the rig's existing deltas.
head = bpy.data.objects['GEO-einar_head']
head_modifier = head.modifiers.new('Rowan cheek and jaw profile', 'NODES')
group = bpy.data.node_groups.new('Rowan cheek and jaw profile', 'GeometryNodeTree')
head_modifier.node_group = group
for direction in ('INPUT', 'OUTPUT'):
    group.interface.new_socket(name='Geometry', in_out=direction, socket_type='NodeSocketGeometry')
nodes, links = group.nodes, group.links
source, sink = nodes.new('NodeGroupInput'), nodes.new('NodeGroupOutput')
set_pos = nodes.new('GeometryNodeSetPosition')
position = nodes.new('GeometryNodeInputPosition')
separate = nodes.new('ShaderNodeSeparateXYZ')
links.new(position.outputs[0], separate.inputs[0])
profile = nodes.new('ShaderNodeMapRange')
profile.inputs['From Min'].default_value = 1.49
profile.inputs['From Max'].default_value = 1.65
profile.inputs['To Min'].default_value = .047
profile.inputs['To Max'].default_value = 0
links.new(separate.outputs['Z'], profile.inputs[0])
multiply = nodes.new('ShaderNodeMath')
multiply.operation = 'MULTIPLY'
links.new(profile.outputs[0], multiply.inputs[0])
links.new(separate.outputs['X'], multiply.inputs[1])
offset = nodes.new('ShaderNodeCombineXYZ')
links.new(multiply.outputs[0], offset.inputs['X'])
links.new(offset.outputs[0], set_pos.inputs['Offset'])
links.new(source.outputs[0], set_pos.inputs['Geometry'])
links.new(set_pos.outputs[0], sink.inputs[0])

def pose(name, channel, samples):
    bone = rig.pose.bones[name]
    for frame, values in samples:
        setattr(bone, channel, values)
        bone.keyframe_insert(data_path=channel, frame=frame, group=name)

pose('FK-Head', 'rotation_euler', [
    (1, (-.017, .045, -.035)), (17, (-.017,.045,-.035)),
    (23, (-.009,.080,-.030)), (31, (.020,.123,-.024)),
    (39, (.039,.138,-.030)), (48, (.041,.135,-.032))])
pose('MSTR-TGT-Eyes', 'location', [
    (1,(-.12,0,.025)), (13,(-.12,0,.025)), (16,(-.41,0,.092)),
    (20,(-.49,0,.036)), (28,(-.52,0,-.086)),
    (34,(-.56,0,-.165)), (48,(-.49,0,-.171))])
pose('FK-Chest','rotation_euler', [
    (1,(.001,0,0)), (12,(.007,0,0)), (25,(.001,0,0)),
    (34,(.006,0,0)), (48,(-.001,0,0))])
for side, asymmetry in [('L',1), ('R',.83)]:
    pose('Blink.'+side, 'location', [
        (1,(0,.00065,0)), (33,(0,.00065,0)), (34,(0,-.006,0)),
        (35,(0,-.0026,0)), (37,(0,.00065,0)), (48,(0,.00065,0))])
    pose('ACT-Eyebrow_Inner.'+side, 'location', [
        (1,(0,-.0021*asymmetry,0)), (16,(0,-.0021*asymmetry,0)),
        (23,(0,-.0014*asymmetry,0)), (34,(0,-.0017*asymmetry,0)),
        (43,(0,-.0007*asymmetry,0)), (48,(0,-.0007*asymmetry,0))])
    pose('ACT-Mouth_Corner.'+side, 'location', [
        (1,(-.0014*asymmetry,0,0)), (34,(-.0014*asymmetry,0,0)),
        (41,(-.0002*asymmetry,0,0)), (48,(-.0002*asymmetry,0,0))])

bpy.ops.object.camera_add(location=(.385,-1.03,1.052))
camera = bpy.context.object
point_at(camera, (.029,-.047,.964))
scene.camera = camera
camera.data.lens = 76
camera.data.dof.use_dof = True
camera.data.dof.focus_distance = (camera.location - Vector((0,-.118,.969))).length
camera.data.dof.aperture_fstop = 6.3

world = bpy.data.worlds.new('Warm afternoon sky')
scene.world = world
world.use_nodes = True
env = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
env.image = bpy.data.images.load(str(assets/'environment/autumn_meadow_1k.hdr'))
bg = world.node_tree.nodes['Background']
world.node_tree.links.new(env.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = .44

def light(name, kind, location, energy, color, target):
    data = bpy.data.lights.new(name, kind)
    data.energy, data.color = energy, color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    point_at(obj, target)
    return data

sun = light('Late sun over the field', 'SUN', (4,2,3.8), 2.25, (1,.77,.51), (0,0,0))
sun.angle = .15
sky = light('Open field sky bounce', 'AREA', (1.2,-1.75,2.35), 68, (.72,.83,1), (0,0,.87))
sky.shape, sky.size = 'DISK', 2
bounce = light('Soft reflected light', 'AREA', (-.7,-1.2,1.45), 15, (1,.84,.69), (0,0,.95))
bounce.size = 1.7

# Oak maps and meadow lighting are from Poly Haven (CC0), as described in assets.
bark = material('Weathered oak', (.17,.11,.07), .9)
tree = bark.node_tree
p = tree.nodes.get('Principled BSDF')
for kind, filename in [('Color','oak_bark_diffuse.jpg'), ('Normal','oak_bark_normal.jpg')]:
    tex = tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(assets/'environment'/filename))
    if kind == 'Normal':
        tex.image.colorspace_settings.name = 'Non-Color'
        normal = tree.nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value = 1.1
        tree.links.new(tex.outputs['Color'], normal.inputs['Color'])
        tree.links.new(normal.outputs[0], p.inputs['Normal'])
    else:
        tree.links.new(tex.outputs['Color'], p.inputs['Base Color'])
verts, faces = [], []
sides, rings = 76, 40
for i in range(rings):
    z = -.15 + i*.115
    for j in range(sides):
        a = 2*pi*j/sides
        radius = (.385 - .023*z + .11*exp(-max(0,z)*8) +
                  .018*sin(5*a+z*.7) + .012*sin(13*a-z*1.5) +
                  .009*sin(26*a+z*2) + .006*sin(35*a-z))
        verts.append((-.374-.023*z+radius*cos(a), .402+radius*sin(a), z))
        if i:
            faces.append(((i-1)*sides+j, (i-1)*sides+(j+1)%sides,
                          i*sides+(j+1)%sides, i*sides+j))
oak = mesh('Oak trunk supporting shoulder', verts, faces, bark)
uv = oak.data.uv_layers.new()
for poly in oak.data.polygons:
    poly.use_smooth = True
    j = poly.index%sides
    i = poly.index//sides
    coords = [(j/sides*3,i*.143),((j+1)/sides*3,i*.143),
              ((j+1)/sides*3,(i+1)*.143),(j/sides*3,(i+1)*.143)]
    for loop, coord in zip(poly.loop_indices, coords):
        uv.data[loop].uv = coord

ground = material('Meadow floor', (.16,.22,.063))
tree = ground.node_tree
nodes, links = tree.nodes, tree.links
coord = nodes.new('ShaderNodeTexCoord')
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.27
noise.inputs['Detail'].default_value = 3.4
links.new(coord.outputs['Object'], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .21
ramp.color_ramp.elements[0].color = (.061,.089,.022,1)
ramp.color_ramp.elements[1].position = .77
ramp.color_ramp.elements[1].color = (.37,.33,.094,1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
links.new(ramp.outputs[0], nodes.get('Principled BSDF').inputs['Base Color'])

def height(x,y):
    return .026*sin(x*.8)*sin(y*1.1)+.36*exp(-((y-11)/5)**2)*(.72+.25*sin(x*.46))

verts = [(x-30,y-7,height(x-30,y-7)) for y in range(46) for x in range(61)]
faces = [(i,i+1,i+62,i+61) for i in range(61*45) if i%61 != 60]
terrain = mesh('Rolling meadow', verts, faces, ground)
for poly in terrain.data.polygons:
    poly.use_smooth = True

grass = [material('Meadow blade '+str(i), color) for i,color in enumerate([
    (.11,.19,.046),(.20,.30,.058),(.28,.34,.078),(.36,.38,.11),(.48,.42,.16)])]

# The gust crosses the field in successive strips. Each blade bends from a fixed root.
for strip in range(14):
    verts, faces, bend, mat_ids = [], [], [], []
    for plant in range(210):
        x = -2.95 + strip*.28 + rng.random()*.29
        y = rng.uniform(.49,7.5)
        if (x+.37)**2 + (y-.40)**2 < .19:
            continue
        base = height(x,y)
        tall = rng.uniform(.084,.36)
        for blade in range(rng.randrange(3,7)):
            a = rng.uniform(0,2*pi)
            dx, dy = cos(a), sin(a)
            h, w = tall*rng.uniform(.62,1.27), rng.uniform(.004,.013)
            lean = rng.uniform(.035,.15)
            start = len(verts)
            for t, width in [(0,.7),(.39,1),(.73,.65),(1,.03)]:
                for edge in (-1,1):
                    verts.append((x+dx*lean*t*t-dy*w*edge*width,
                                  y+dy*lean*t*t+dx*w*edge*width,base+h*t))
                    bend.append(h*t*t)
            tone = rng.randrange(len(grass))
            for j in (0,2,4):
                faces.append((start+j,start+j+1,start+j+3,start+j+2))
                mat_ids.append(tone)
    patch = mesh('Field grasses %02d'%strip, verts, faces)
    for mat in grass:
        patch.data.materials.append(mat)
    for p, index in zip(patch.data.polygons, mat_ids):
        p.material_index = index
    patch.shape_key_add(name='Rest')
    shape = patch.shape_key_add(name='Downwind flex')
    flex = [coordinate for (x, y, z), amplitude in zip(verts, bend)
            for coordinate in (x + .64*amplitude, y + .24*amplitude, z - .17*amplitude)]
    shape.data.foreach_set('co', flex)
    for f in range(1,49):
        delay = strip*.56
        t = f - delay
        pulse = exp(-((t-21)/6.3)**2)
        tail = exp(-((t-30)/9)**2)
        shape.value = max(0, .025+.72*pulse*(.74+.26*sin(t*.77))+
                          .15*tail*sin(t*.68)+.035*sin(f*.39+strip*.77))
        shape.keyframe_insert(data_path='value', frame=f)

# Windborne oak leaves. The closest leaf uses a fixed path beside the face
# so the eye-line remains legible while the leaf rolls in and out of the light.
leaf_mats = [material('Dry ochre leaf', (.57,.22,.045), .65),
             material('Russet leaf', (.30,.075,.018), .75),
             material('Leaf ridge', (.64,.30,.079), .71)]
for mat in leaf_mats[:2]:
    mat.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value = .06

def leaf(name, size, tone):
    widths = [0,.19,.34,.27,.41,.29,.35,.19,.095,0]
    verts, faces = [], []
    for i,w in enumerate(widths):
        t = i/(len(widths)-1)
        for j in (-1,0,1):
            verts.append((j*w*size, (t-.48)*size,
                          size*(.19*(t-.48)**2-.20*w*abs(j)+.065*j*sin(t*6))))
        if i:
            k = 3*(i-1)
            faces.extend([(k,k+1,k+4,k+3),(k+1,k+2,k+5,k+4)])
    obj = mesh(name, verts, faces, leaf_mats[tone])
    obj.data.materials.append(leaf_mats[2])
    for p in obj.data.polygons:
        p.use_smooth = True
    vein_vertices = []
    for i in range(len(widths)):
        _, y, z = verts[i*3+1]
        vein_vertices.extend([(-size*.013,y,z+size*.003),(size*.013,y,z+size*.003)])
    vein = mesh(name+' midrib', vein_vertices,
                [(j,j+1,j+3,j+2) for j in range(0,len(vein_vertices)-2,2)], leaf_mats[2])
    vein.parent = obj
    return obj

orientation = camera.rotation_euler.to_matrix()
for index, (start,depth,x,z,speed,size) in enumerate([
    (12,.93,.110,.126,.0083,.038),
    (13,1.27,.23,.155,.0092,.047),
    (17,1.60,.235,.22,.0103,.051),
    (19,2.20,.352,.29,.0130,.065),
    (23,1.35,.245,.175,.0071,.041),
    (28,1.77,.298,.226,.0094,.057),
]):
    obj = leaf('Tracked oak leaf' if index == 0 else 'Airborne oak leaf %d'%index, size, index%2)
    for f in range(1,49):
        t = f-start
        swing = sin(t*.31+index*1.6)
        drift = .0022*t + .012*swing
        descent = speed*t + speed*.18*sin(t*.49+index)
        obj.location = camera.location + orientation @ Vector(
            (x+drift,z-descent,-depth+.031*cos(t*.26+index)))
        obj.rotation_euler = (1.0+.67*sin(t*.39+index),
                              .52*cos(t*.27+index),t*.19+index)
        obj.keyframe_insert(data_path='location', frame=f)
        obj.keyframe_insert(data_path='rotation_euler', frame=f)

for frame, name in [(1,'Still in the shade'),(13,'Wind arrives'),
                    (16,'Eyes find the leaf'),(20,'Head follows'),(34,'Blink'),
                    (41,'Expression settles')]:
    scene.timeline_markers.new(name, frame=frame)
scene.frame_set(1)
