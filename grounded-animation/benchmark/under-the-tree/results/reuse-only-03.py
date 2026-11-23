"""Build Under the Tree in Blender 5.2.

Einar Rig (CC BY 4.0) Blender Foundation | studio.blender.org.
Adapted for this shot. https://creativecommons.org/licenses/by/4.0/
https://studio.blender.org/characters/einar/v1/
Poly Haven, CC0:
Jolcham Oak Bark 01 (Charlotte Baglioni) https://polyhaven.com/a/jolcham_oak_bark_01
Grass Medium 01 (Rico Cilliers and Rob Tuytel) https://polyhaven.com/a/grass_medium_01
Autumn Meadow (Sergej Majboroda) https://polyhaven.com/a/autumn_meadow
"""
from pathlib import Path
from math import cos, sin, pi, exp
from random import Random

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
ENV = ASSETS / 'environment'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.eevee.taa_render_samples = 24
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'
rng = Random(11027)

with bpy.data.libraries.load(str(ASSETS / 'einar.blend'), link=False) as (_, target):
    target.collections = ['CH-einar']
scene.collection.children.link(target.collections[0])
rig = bpy.data.objects['RIG-einar']
rig.name = 'Rowan • facial performance'
rig.animation_data.action = None
rig.location.z = -.51
head = bpy.data.objects['GEO-einar_head']
profile = head.shape_key_add(name='Rowan • nose bridge and cheek structure')
basis = head.data.shape_keys.reference_key
for point, original in zip(profile.data, basis.data):
    x, y, z = original.co
    # Leave the lids, lips and teeth registration to the original facial rig.
    bridge = exp(-((x/.018)**2 + ((y+.147)/.034)**2 + ((z-1.615)/.026)**2))
    cheek = exp(-(((abs(x)-.062)/.032)**2 + ((z-1.594)/.037)**2))
    point.co.y -= .008*bridge
    point.co.x += .004*cheek*(1 if x > 0 else -1)
profile.value = 1.0
for obj in target.collections[0].all_objects:
    if obj.name.startswith('WGT-') or obj.name.endswith('.messy'):
        obj.hide_render = True

def surface(name, color, roughness=.65):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return material, shader

# Expose the lips and jaw for the close-up.
for obj in list(bpy.data.objects):
    if obj.type == 'CURVES' and obj.name.startswith(('GEO-einar_mustache', 'GEO-einar_beard')):
        bpy.data.objects.remove(obj, do_unlink=True)

hair, shader = surface('Rowan • brown and silver hair', (.082,.047,.027), .68)
shader.inputs['Specular IOR Level'].default_value = .18
nodes, links = hair.node_tree.nodes, hair.node_tree.links
strand = nodes.new('ShaderNodeHairInfo')
colors = nodes.new('ShaderNodeValToRGB')
colors.color_ramp.elements[0].color = (.017,.010,.006,1)
colors.color_ramp.elements[1].color = (.23,.17,.11,1)
colors.color_ramp.elements[1].position = .98
colors.color_ramp.elements.new(.77).color = (.063,.035,.017,1)
links.new(strand.outputs['Random'], colors.inputs[0])
links.new(colors.outputs[0], shader.inputs['Base Color'])
for part in ('eyebrows','hair'):
    bpy.data.objects['GEO-einar_'+part].data.materials[0] = hair

# Recolor the costume while retaining its weave, seams and weathering.
for name, tint in [('einar.jacket.canvas', (.42,.71,.78,1)),
                   ('einar.jacket.collar', (.44,.70,.72,1)),
                   ('einar.hat', (.83,.40,.20,1))]:
    mat = bpy.data.materials.get(name)
    if mat and mat.use_nodes:
        tree = mat.node_tree
        for shader in list(tree.nodes):
            if shader.type != 'BSDF_PRINCIPLED':
                continue
            base = shader.inputs['Base Color']
            if base.is_linked:
                source = base.links[0].from_socket
                mix = tree.nodes.new('ShaderNodeMixRGB')
                mix.blend_type = 'MULTIPLY'
                mix.inputs[0].default_value = 1
                mix.inputs[2].default_value = tint
                tree.links.new(source, mix.inputs[1])
                tree.links.new(mix.outputs[0], base)

def pose(name, channel, keys):
    bone = rig.pose.bones[name]
    for frame, value in keys:
        setattr(bone, channel, value)
        bone.keyframe_insert(data_path=channel, frame=frame, group=name)

pose('FK-Head', 'rotation_euler', [
    (1, (-.010, .032,.011)), (13, (-.008,.032,.012)),
    (19, (-.008,.032,.012)), (25, (.010,.090,.002)),
    (32, (.037,.110,-.008)), (39, (.047,.101,-.010)),
    (48, (.049,.098,-.010))])
# Shared eye target is roughly one metre in front of the corneas.
gaze = rig.pose.bones['MSTR-TGT-Eyes']
rest = gaze.bone.matrix_local.to_3x3().inverted()
pose(gaze.name, 'location', [(f, rest @ Vector(v)) for f,v in [
    (1,(.015,0,.024)), (14,(.015,0,.024)), (17,(.18,0,.068)),
    (22,(.255,0,.024)), (28,(.29,0,-.072)), (33,(.26,0,-.158)),
    (37,(.233,0,-.182)), (48,(.213,0,-.172))]])
for side in ('L', 'R'):
    pose('Blink.'+side, 'location', [
        (1,(0,.0007,0)), (32,(0,.0005,0)), (34,(0,-.006,0)),
        (36,(0,.0004,0)), (39,(0,0,0)), (48,(0,0,0))])
    pose('ACT-Eyebrow_Inner.'+side, 'location', [
        (1,(0,-.0024,0)), (15,(0,-.0024,0)), (20,(0,-.0013,0)),
        (31,(0,-.0019,0)), (39,(0,-.0006,0)), (48,(0,-.0006,0))])
    pose('ACT-Mouth_Corner.'+side, 'location', [
        (1,(0,-.0015,0)), (31,(0,-.0015,0)), (41,(0,-.00015,0)),
        (48,(0,-.00015,0))])
pose('MSTR-Spine_Chest', 'rotation_euler', [
    (1,(-.018,0,0)),(13,(-.014,0,.001)),(26,(-.018,0,0)),
    (39,(-.014,0,.001)),(48,(-.016,0,0))])

def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

bpy.ops.object.camera_add(location=(.59,-1.33,1.186))
camera = bpy.context.object
camera.name = 'Locked portrait'
aim(camera, (.087,-.12,1.144))
camera.data.lens = 96
camera.data.clip_end = 220
camera.data.dof.use_dof = True
camera.data.dof.focus_distance = (camera.location - Vector((0,-.132,1.165))).length
camera.data.dof.aperture_fstop = 5.6
scene.camera = camera

world = bpy.data.worlds.new('Autumn afternoon')
world.use_nodes = True
scene.world = world
nodes = world.node_tree.nodes
links = world.node_tree.links
environment = nodes.new('ShaderNodeTexEnvironment')
environment.image = bpy.data.images.load(str(ENV / 'autumn_meadow_1k.hdr'))
rotation = nodes.new('ShaderNodeVectorRotate')
rotation.rotation_type = 'Z_AXIS'
rotation.inputs['Angle'].default_value = 1.9
links.new(nodes.new('ShaderNodeTexCoord').outputs['Generated'], rotation.inputs[0])
links.new(rotation.outputs[0], environment.inputs[0])
links.new(environment.outputs[0], nodes.get('Background').inputs[0])
nodes.get('Background').inputs[1].default_value = .64

def light(name, kind, position, target, color, power, size):
    data = bpy.data.lights.new(name, kind)
    data.color, data.energy = color, power
    if kind == 'AREA':
        data.shape = 'DISK'
        data.size = size
    else:
        data.angle = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    aim(obj, target)

light('Open sky through the canopy','AREA',(.12,-2,2.45),(0,0,1.13),(.76,.86,1),88,2.35)
light('Sky bounce beneath the brim','AREA',(.10,-1.67,1.26),(0,0,1.14),(.83,.91,1),19,1.35)
light('Warm bounce from meadow','AREA',(1.45,-.3,1.52),(0,0,1.1),(1,.78,.53),29,1.4)
light('Late sun through branches','AREA',(1.22,.92,2.24),(0,0,1.21),(1,.75,.50),133,.85)
light('Sun over the field','SUN',(3,1,4),(0,0,0),(1,.84,.65),1.05,.15)

def mesh(name, vertices, faces, material=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    if material:
        data.materials.append(material)
    return obj

bark, bark_shader = surface('Jolcham oak • fissured bark', (.18,.11,.065),.85)
nodes, links = bark.node_tree.nodes, bark.node_tree.links
coords = nodes.new('ShaderNodeTexCoord')
diffuse = nodes.new('ShaderNodeTexImage')
diffuse.image = bpy.data.images.load(str(ENV / 'oak_bark_diffuse.jpg'))
normal = nodes.new('ShaderNodeTexImage')
normal.image = bpy.data.images.load(str(ENV / 'oak_bark_normal.jpg'))
normal.image.colorspace_settings.name = 'Non-Color'
normal_map = nodes.new('ShaderNodeNormalMap')
normal_map.inputs['Strength'].default_value = 1.1
for image in (diffuse,normal):
    links.new(coords.outputs['UV'], image.inputs[0])
shade = nodes.new('ShaderNodeMixRGB')
shade.blend_type = 'MULTIPLY'
shade.inputs[0].default_value = 1
shade.inputs[2].default_value = (.65,.64,.59,1)
links.new(diffuse.outputs[0], shade.inputs[1])
links.new(shade.outputs[0], bark_shader.inputs['Base Color'])
links.new(normal.outputs[0], normal_map.inputs['Color'])
links.new(normal_map.outputs[0], bark_shader.inputs['Normal'])

verts, faces = [], []
segments, levels = 96, 35
for j in range(levels):
    z = -.16 + j*.091
    for i in range(segments):
        a = 2*pi*i/segments
        r = .34+.095*exp(-4*max(z,0))-.025*z
        r += .022*cos(7*a+z)+.011*sin(13*a-z*2)+.008*sin(26*a+z)
        verts.append((-.215-.105*z+r*cos(a), .407+r*sin(a), z))
        if j:
            k = (i+1)%segments
            faces.append(((j-1)*segments+i,(j-1)*segments+k,j*segments+k,j*segments+i))
trunk = mesh('Oak trunk at his shoulder', verts, faces, bark)
uv = trunk.data.uv_layers.new()
for polygon in trunk.data.polygons:
    row, col = divmod(polygon.index,segments)
    polygon.use_smooth = True
    for loop, (i,j) in zip(polygon.loop_indices,((col,row),(col+1,row),(col+1,row+1),(col,row+1))):
        uv.data[loop].uv = (i/segments*2.05,j*.091)

ground, shader = surface('Meadow soil and low grass',(.22,.24,.085))
nodes, links = ground.node_tree.nodes, ground.node_tree.links
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = .64
links.new(nodes.new('ShaderNodeTexCoord').outputs['Object'],noise.inputs[0])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (.072,.093,.021,1)
ramp.color_ramp.elements[1].color = (.39,.30,.093,1)
links.new(noise.outputs['Fac'],ramp.inputs[0])
links.new(ramp.outputs[0],shader.inputs['Base Color'])
mesh('Open field', [(-30,-7,-.06),(42,-7,-.06),(42,70,.40),(-30,70,.40)],[(0,1,2,3)],ground)

bpy.ops.import_scene.gltf(filepath=str(ENV / 'grass' / 'grass_medium_01_1k.gltf'))
sources = [o for o in bpy.context.selected_objects if o.type == 'MESH']
bpy.context.view_layer.update()
camera_basis = camera.rotation_euler.to_matrix()
# Each strip shares a slightly delayed bending deformation.
for source in sources:
    source.hide_render = True
variants = ('small_a', 'mid_b', 'tall_a', 'tall_c')
for index, variant in enumerate(variants):
    source = next(o for o in sources if o.name == f'grass_medium_01_{variant}_LOD0')
    orientation = source.matrix_world.to_3x3().to_4x4()
    for strip in range(7):
        data = source.data.copy()
        data.transform(orientation)
        for j in range(12):
            tuft = bpy.data.objects.new('Meadow tuft', data)
            scene.collection.objects.link(tuft)
            depth = 4.8 + strip*1.68 + rng.uniform(-.85,.85)
            offset = rng.uniform(.12,.62)*depth*camera.data.sensor_width/camera.data.lens
            placement = camera.location + camera_basis @ Vector((offset,0,-depth))
            tuft.location = (placement.x,placement.y,-.05+placement.y*.006)
            scale = rng.uniform(.89,1.66)
            tuft.scale = (scale,scale,scale*rng.uniform(.8,1.24))
            tuft.rotation_euler.z = rng.uniform(-.55,.55)
            if j == 0:
                tuft.shape_key_add(name='Still')
                bend = tuft.shape_key_add(name='Breeze')
                low = min(v.co.z for v in data.vertices)
                high = max(v.co.z for v in data.vertices)
                for v in bend.data:
                    height = (v.co.z-low)/max(.01,high-low)
                    v.co.x += .36*(high-low)*height**2
                for frame in range(1,50,2):
                    t = (frame-1)/12
                    u = t-.059*strip
                    envelope = exp(-((u-1.83)/.62)**4)
                    bend.value = .025 + envelope*(.53+.43*sin(7.7*u+index))
                    bend.keyframe_insert(data_path='value',frame=frame)

# Thin alternating lobes, a raised midrib, and russet-to-gold variations.
leaf_mats = [surface('Oak leaf '+name,color,.57)[0] for name,color in [
    ('amber',(.48,.19,.027)), ('russet',(.30,.075,.019)),
    ('straw',(.57,.33,.065)),('veins',(.28,.14,.045))]]

def oak_leaf(name, length, palette):
    outline = [(0,-.51),(.10,-.37),(.26,-.32),(.30,-.21),(.17,-.16),
               (.36,-.085),(.37,.04),(.20,.095),(.32,.20),(.26,.29),
               (.13,.30),(.16,.41),(0,.51)]
    outline += [(-x*.93,y+.013) for x,y in reversed(outline[1:-1])]
    vertices = [(0,0,.080*length)]
    vertices += [(x*length,y*length,(.035*sin(y*6)+.047*abs(x))*length)
                 for x,y in outline]
    vertices += [(-.014*length,-.64*length,0),(.014*length,-.64*length,0),
                 (.017*length,-.44*length,.015*length),(-.016*length,-.44*length,.015*length)]
    count = len(outline)
    obj = mesh(name,vertices,[(0,i+1,(i+1)%count+1) for i in range(count)]
               +[(count+1,count+2,count+3,count+4)],leaf_mats[palette])
    obj.data.materials.append(leaf_mats[3])
    obj.data.polygons[-1].material_index = 1
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    solid = obj.modifiers.new('Thin leaf tissue','SOLIDIFY')
    solid.thickness = .00031
    return obj

bpy.context.view_layer.update()
def projected_position(x,y,distance):
    width = distance*camera.data.sensor_width/camera.data.lens
    return camera.location + camera_basis @ Vector((x*width,y*width*9/16,-distance))

for i in range(9):
    featured = i == 0
    leaf = oak_leaf('Leaf he follows' if featured else 'Falling oak leaf', .043 if featured
                    else rng.uniform(.033,.083),i%3)
    start = 1.15 if featured else rng.uniform(.80,2.76)
    speed = .63 if featured else rng.uniform(.32,.79)
    x0 = .215 if featured else .155 + .048*i + rng.uniform(-.034,.034)
    distance = 1.21 if featured else rng.uniform(1.55,3.5)
    phase = rng.uniform(0,2*pi)
    for f in range(1,50,2):
        t = (f-1)/12-start
        x = x0 + (.078 if featured else .044)*t + .024*sin(t*5+phase)
        y = .62 - speed*t + .035*sin(5*t+phase)
        leaf.location = projected_position(x,y,distance+.035*sin(4*t+phase))
        leaf.rotation_euler = (1.26+.48*sin(t*5+phase),
                               .55*cos(t*6+phase),phase+t*(2.1+i*.27))
        leaf.keyframe_insert(data_path='location',frame=f)
        leaf.keyframe_insert(data_path='rotation_euler',frame=f)

for frame,name in [(1,'In the shade'),(13,'The breeze gathers'),(18,'Eyes find the leaf'),
                   (24,'Head follows'),(32,'Wind settles'),(34,'Blink'),(42,'Hold')]:
    scene.timeline_markers.new(name,frame=frame)
scene.frame_set(1)
