"""Under the Tree. Build with Blender 5.2 from factory startup.

Face rig adapted from Einar Rig (CC BY 4.0) Blender Foundation,
https://studio.blender.org/characters/einar/v1/
Oak maps and autumn meadow environment from Poly Haven (CC0).
"""
from math import cos, exp, pi, sin
from pathlib import Path
from random import Random

import bpy
from mathutils import Vector

assets = Path(__file__).resolve().parent / "assets"
environment = assets / "environment"
rng = Random(98)
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
scene.view_settings.look = 'AgX - Medium High Contrast'

with bpy.data.libraries.load(str(assets / 'einar.blend'), link=False) as (_, target):
    target.collections = ['CH-einar']
character, = target.collections
scene.collection.children.link(character)
rig = bpy.data.objects['RIG-einar']
if rig.animation_data:
    rig.animation_data.action = None
    rig.animation_data.use_nla = False
rig.location.z = -.72
rig.rotation_euler.x = -.075
rig.name = 'Rowan | performance rig'

def material(name, color, roughness=.75):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return mat, shader

def tint(name, color, amount):
    mat = bpy.data.materials.get(name)
    if mat is None:
        return
    trees = [mat.node_tree]
    if not any(n.type == 'BSDF_PRINCIPLED' for n in mat.node_tree.nodes):
        for node in mat.node_tree.nodes:
            if node.type == 'GROUP':
                node.node_tree = node.node_tree.copy()
                trees.append(node.node_tree)
    for tree in trees:
        for shader in list(tree.nodes):
            if shader.type != 'BSDF_PRINCIPLED':
                continue
            socket = shader.inputs['Base Color']
            mix = tree.nodes.new('ShaderNodeMixRGB')
            mix.blend_type = 'MULTIPLY'
            mix.inputs[0].default_value = amount
            if socket.is_linked:
                tree.links.new(socket.links[0].from_socket, mix.inputs[1])
            else:
                mix.inputs[1].default_value = socket.default_value
            mix.inputs[2].default_value = (*color, 1)
            tree.links.new(mix.outputs[0], socket)

# Recolor the supplied canvas shader inside its material group to keep its weave.
tint('einar.jacket.canvas', (.22, .53, .56), .96)
tint('einar.jacket.collar', (.30, .54, .57), .79)
tint('einar.hat', (.46, .27, .15), .83)
tint('einar.skin', (1, .84, .69), .27)
tint('einar.hair', (.68, .50, .34), .50)
tint('eyes.iris', (.55, 1, .68), .65)

def pose(name, prop, values):
    bone = rig.pose.bones[name]
    for frame, value in values:
        setattr(bone, prop, value)
        bone.keyframe_insert(data_path=prop, frame=frame, group=name)

pose('FK-Head', 'rotation_euler', [
    (1, (.012, -.045, -.034)), (17, (.013, -.044, -.035)),
    (21, (.015, -.037, -.032)), (29, (.058, .041, -.025)),
    (35, (.074, .058, -.023)), (48, (.071, .056, -.022)),
])
pose('MSTR-TGT-Eyes', 'location', [
    (1, (-.11, 0, .016)), (15, (-.112, 0, .016)),
    (18, (-.275, 0, .041)), (24, (-.312, 0, -.016)),
    (32, (-.35, 0, -.151)), (36, (-.317, 0, -.194)),
    (43, (-.283, 0, -.148)), (48, (-.28, 0, -.148)),
])
pose('MSTR-Spine_Chest', 'rotation_euler', [
    (1, (.003, 0, 0)), (11, (.010, 0, .001)), (26, (.002, 0, 0)),
    (39, (.009, 0, .001)), (48, (.006, 0, 0)),
])
pose('MSTR-Jaw', 'rotation_euler', [
    (1, (0, 0, 0)), (34, (0, 0, 0)), (41, (.013, 0, 0)), (48, (.013, 0, 0)),
])
for side, sign in [('L', 1), ('R', -1)]:
    pose('Blink.' + side, 'location', [
        (1, (0, -.00035, 0)), (34, (0, -.00035, 0)),
        (35.4, (0, -.0037, 0)), (36, (0, -.006, 0)),
        (36.55, (0, -.0057, 0)), (38, (0, .00005, 0)), (48, (0, .00005, 0)),
    ])
    pose('ACT-Eyebrow_Inner.' + side, 'location', [
        (1, (-sign*.0011, -.0018, 0)), (16, (-sign*.0011, -.0020, 0)),
        (24, (-sign*.0006, -.0008, 0)), (34, (-sign*.0008, -.0011, 0)),
        (43, (0, -.0003, 0)), (48, (0, -.0003, 0)),
    ])
    pose('ACT-Mouth_Corner.' + side, 'location', [
        (1, (sign*.0012, -.00065, 0)), (33, (sign*.0012, -.00065, 0)),
        (42, (0, .00012, 0)), (48, (0, .00012, 0)),
    ])

def mesh_object(name, vertices, faces, mats):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(ob)
    for mat in mats:
        mesh.materials.append(mat)
    return ob

def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()

bpy.ops.object.camera_add(location=(.268, -.736, .974))
camera = bpy.context.object
camera.name = 'Locked portrait'
aim(camera, (.041, -.045, .915))
camera.data.lens = 66
camera.data.dof.use_dof = True
camera.data.dof.focus_distance = .79
camera.data.dof.aperture_fstop = 5.6
scene.camera = camera

# The trunk leans into the upper back. Its fluted cross section changes up the bole.
bark, bs = material('Oak | ridged bark', (.15, .10, .058))
nodes, links = bark.node_tree.nodes, bark.node_tree.links
uv = nodes.new('ShaderNodeTexCoord')
for filename, output in [('oak_bark_diffuse.jpg', 'Base Color'), ('oak_bark_normal.jpg', 'Normal')]:
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(environment / filename))
    links.new(uv.outputs['UV'], tex.inputs['Vector'])
    if output == 'Normal':
        tex.image.colorspace_settings.name = 'Non-Color'
        normal = nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value = 1.25
        links.new(tex.outputs['Color'], normal.inputs['Color'])
        links.new(normal.outputs['Normal'], bs.inputs[output])
    else:
        links.new(tex.outputs['Color'], bs.inputs[output])

vertices, faces = [], []
rings, sides = 38, 128
for j in range(rings):
    z = -.17 + j*.112
    for i in range(sides):
        a = 2*pi*i/sides
        radius = .345 - .018*z + .11*exp(-max(0,z)*5)
        radius += .019*sin(7*a+z*.8) + .009*sin(19*a-z*1.5) + .004*sin(37*a+z*2.1)
        vertices.append((-.338-.075*z + radius*cos(a), .415+.064*z + radius*sin(a), z))
for j in range(rings-1):
    for i in range(sides):
        a = j*sides+i
        b = j*sides+(i+1)%sides
        faces.append((a,b,b+sides,a+sides))
trunk = mesh_object('Old oak', vertices, faces, [bark])
layer = trunk.data.uv_layers.new()
for poly in trunk.data.polygons:
    poly.use_smooth = True
    j, i = divmod(poly.index, sides)
    for loop, (x,y) in zip(poly.loop_indices, [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]):
        layer.data[loop].uv = (x/sides*3.2, y*.112*1.6)

def surface(x, y):
    return .09*sin(x*.44+y*.32)+.06*sin(y*.74-x*.27)+.015*y

soil, bs = material('Meadow | earth and low cover', (.19,.21,.052))
nodes, links = soil.node_tree.nodes, soil.node_tree.links
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 3.8
noise.inputs['Detail'].default_value = 4
coord = nodes.new('ShaderNodeTexCoord')
links.new(coord.outputs['Object'], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .22
ramp.color_ramp.elements[0].color = (.097,.106,.026,1)
ramp.color_ramp.elements[1].position = .76
ramp.color_ramp.elements[1].color = (.36,.33,.092,1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
links.new(ramp.outputs[0], bs.inputs['Base Color'])
vertices = [(x,y,surface(x,y)) for y in range(-4,49) for x in range(-28,25)]
faces = [(j*53+i,j*53+i+1,(j+1)*53+i+1,(j+1)*53+i) for j in range(52) for i in range(52)]
ground = mesh_object('Rolling meadow', vertices, faces, [soil])
for poly in ground.data.polygons:
    poly.use_smooth = True

greens = [material('Field plant | '+name, color)[0] for name,color in [
    ('olive',(.245,.295,.062)), ('green',(.13,.22,.046)), ('straw',(.48,.375,.105)),
    ('seed',(.55,.37,.111)), ('sage',(.265,.33,.13)), ('dry',(.47,.24,.053)),
]]

# Each patch bends through its blade length, with pinned bases and staggered gust arrival.
for patch in range(24):
    vertices, flex, faces, colors = [], [], [], []
    ox = -2.5 + (patch%8)*.64
    oy = 1.0 + (patch//8)*1.9
    for plant in range(340):
        x, y = ox+rng.uniform(-.36,.36), oy+rng.uniform(0,1.93)
        z = surface(x,y)-.025
        if x*x+(y-.4)**2 < .27:
            continue
        h = rng.uniform(.15,.58)
        a = rng.uniform(0,2*pi)
        dx,dy = cos(a),sin(a)
        width = rng.uniform(.009,.029)
        lean = rng.uniform(.08,.35)*h
        color = rng.choices([0,1,2,4,5],[4,4,2,2,1])[0]
        start = len(vertices)
        for k in range(5):
            t = k/4
            w = width*(1-.97*t)*.5
            p = (x+dx*lean*t*t,y+dy*lean*t*t,z+h*(t-.12*t*t))
            vertices.extend([(p[0]-dy*w,p[1]+dx*w,p[2]),(p[0]+dy*w,p[1]-dx*w,p[2])])
            flex.extend([h*t*t]*2)
            if k:
                b = start+2*k
                faces.append((b-2,b-1,b+1,b))
                colors.append(color)
        if plant%13 == 0:
            end = Vector(p)
            start = len(vertices)
            vertices.extend([end+Vector(v) for v in [(-.009,0,-.025),(.012,0,.016),(0,.009,.064),(-.012,0,.041),(0,-.01,.024)]])
            flex.extend([h]*5)
            faces.extend([(start,start+1,start+2,start+3),(start,start+4,start+2,start+3)])
            colors.extend([3,3])
    ob = mesh_object('Meadow plants %02d'%patch, vertices, faces, greens)
    for polygon,index in zip(ob.data.polygons, colors):
        polygon.material_index = index
    ob.shape_key_add(name='Rest')
    bend = ob.shape_key_add(name='Wind bend')
    for point, amount in zip(bend.data, flex):
        point.co += Vector((.64*amount,.23*amount,-.16*amount))
    delay = (patch%8)*.75+(patch//8)*1.1
    for frame in range(1,49):
        t = frame-delay
        envelope = exp(-((t-22)/7.4)**2)
        bend.value = .035 + .79*envelope*(.68+.32*sin(t*.81+oy*.36))
        bend.keyframe_insert(data_path='value',frame=frame)

world = bpy.data.worlds.new('Late afternoon sky')
scene.world = world
nodes, links = world.node_tree.nodes, world.node_tree.links
sky = nodes.new('ShaderNodeTexEnvironment')
sky.image = bpy.data.images.load(str(environment / 'autumn_meadow_1k.hdr'))
coord = nodes.new('ShaderNodeTexCoord')
rotate = nodes.new('ShaderNodeVectorRotate')
rotate.rotation_type = 'Z_AXIS'
rotate.inputs['Angle'].default_value = 1.15
links.new(coord.outputs['Normal'], rotate.inputs['Vector'])
links.new(rotate.outputs['Vector'], sky.inputs['Vector'])
links.new(sky.outputs['Color'], nodes.get('Background').inputs['Color'])
nodes.get('Background').inputs['Strength'].default_value = .65

def light(name, kind, location, point, power, color, size):
    data = bpy.data.lights.new(name, kind)
    data.energy = power
    data.color = color
    ob = bpy.data.objects.new(name,data)
    scene.collection.objects.link(ob)
    ob.location = location
    aim(ob,point)
    if kind == 'AREA':
        data.shape = 'DISK'
        data.size = size
    else:
        data.angle = size

light('Open sky | broad cool key','AREA',(1.7,-1.5,2.48),(0,0,.96),89,(.78,.87,1),2.5)
light('Meadow bounce','AREA',(-.5,-.82,.57),(0,0,.94),10,(1,.76,.54),1.1)
light('Late sun across field','SUN',(2.2,4.1,2.9),(0,0,.55),2.15,(1,.74,.44),.075)
light('Canopy break | edge light','AREA',(.87,.63,1.52),(0,-.04,.92),24,(1,.71,.41),.47)

# A local camera lane keeps all descending leaves to the open side of the portrait.
def make_leaf(name, length, color):
    mat, shader = material(name+' | lamina', color, .62)
    shader.inputs['Subsurface Weight'].default_value = .13
    midrib, _ = material(name+' | veins', tuple(x*1.35 for x in color))
    outline = [(0,-.48),(.13,-.38),(.19,-.28),(.26,-.24),(.24,-.16),
               (.34,-.10),(.29,-.02),(.38,.04),(.32,.10),(.31,.18),
               (.23,.21),(.24,.29),(.13,.33),(0,.52)]
    shape = outline + [(-x,y) for x,y in reversed(outline[1:-1])]
    vertices = [(x*length,y*length,length*(.86*x*x-.23*y*y+.14*x*y)) for x,y in shape]
    center = len(vertices)
    vertices.append((0,0,0))
    faces = [(center,i,(i+1)%center) for i in range(center)]
    ob = mesh_object(name, vertices, faces, [mat,midrib])
    solid = ob.modifiers.new('Leaf thickness','SOLIDIFY')
    solid.thickness = .00035
    vein = bpy.data.curves.new(name+' | rib','CURVE')
    vein.dimensions = '3D'
    vein.bevel_depth = length*.007
    vein.bevel_resolution = 1
    for points in [[(0,-.66,-.095),(0,-.47,-.046),(0,0,.009),(0,.48,-.04)]] + [
        [(0,y,.012-.23*y*y),(s*w*.6,y+.07,.018),(s*w,y+.13,.024)]
        for s in [-1,1] for y,w in [(-.30,.17),(-.13,.25),(.04,.27),(.18,.16)]
    ]:
        spline = vein.splines.new('POLY')
        spline.points.add(len(points)-1)
        for point,co in zip(spline.points,points):
            point.co = (*(length*x for x in co),1)
    vein.materials.append(midrib)
    rib = bpy.data.objects.new(vein.name,vein)
    scene.collection.objects.link(rib)
    rib.parent = ob
    return ob

bpy.context.view_layer.update()
for index, (start, depth, lateral, velocity, length, color) in enumerate([
    (13,.94,.100,.146,.039,(.59,.255,.048)),
    (10,1.59,.236,.238,.060,(.52,.30,.073)),
    (19,1.30,.259,.117,.046,(.33,.20,.043)),
    (24,1.96,.200,.102,.059,(.51,.40,.072)),
    (29,1.16,.182,.101,.030,(.57,.21,.043)),
    (15,2.37,.377,.211,.066,(.44,.24,.041)),
    (33,1.45,.269,.122,.042,(.47,.32,.075)),
]):
    leaf = make_leaf('Amber leaf %02d'%index,length,color)
    for frame in range(1,49):
        t = (frame-start)/12
        phase = t*7 + index*1.61
        x = lateral + .027*t + .013*sin(phase)
        y = depth*.166 - velocity*t + .011*cos(phase*1.3)
        d = depth+.027*sin(phase*.8)
        leaf.location = camera.matrix_world @ Vector((x,y,-d))
        leaf.rotation_euler = (.54+1.05*sin(phase),t*2.9+index,.75*sin(t*4+index)+t*1.5)
        leaf.keyframe_insert(data_path='location',frame=frame)
        leaf.keyframe_insert(data_path='rotation_euler',frame=frame)

for label, frame in [('Watching',1),('Breeze enters',13),('Eyes find leaf',18),
                     ('Head follows',22),('Breeze fades',32),('Blink',36),('Hold',43)]:
    scene.timeline_markers.new(label, frame=frame)
scene['Character credit'] = 'Adapted from Einar Rig (CC BY 4.0), Blender Foundation | studio.blender.org'
def lid_gap(frame):
    scene.frame_set(frame)
    upper = rig.pose.bones['Eyelid_Upper_2.L'].head
    lower = rig.pose.bones['Eyelid_Lower_2.L'].head
    return (upper - lower).length

assert lid_gap(36) < .35 * lid_gap(34), 'Eyelid drivers did not close the blink'
scene.frame_set(1)
