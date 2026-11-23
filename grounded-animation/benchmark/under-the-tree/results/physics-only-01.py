"""Under the Tree. Run with Blender --background --factory-startup --python scene.py."""
from array import array
from math import cos, exp, pi, radians, sin
from pathlib import Path
from random import Random

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
RNG = Random(1186)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 32
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.unit_settings.system = 'METRIC'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'

def group(name):
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    return collection

set_col = group('01 • Oak and field')
wind_col = group('02 • Wind in the meadow')
leaf_col = group('03 • Falling oak leaves')
shot_col = group('04 • Camera and late-afternoon light')

def mesh(name, vertices, faces, collection, materials):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    for material in materials:
        data.materials.append(material)
    return obj

def surface(name, a, b=None, scale=10, rough=.7, bump=0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*a, 1)
    bsdf.inputs['Roughness'].default_value = rough
    if b is not None:
        tex = nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = scale
        tex.inputs['Detail'].default_value = 4
        coords = nodes.new('ShaderNodeTexCoord')
        links.new(coords.outputs['Object'], tex.inputs['Vector'])
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = .22
        ramp.color_ramp.elements[0].color = (*a, 1)
        ramp.color_ramp.elements[1].position = .79
        ramp.color_ramp.elements[1].color = (*b, 1)
        links.new(tex.outputs['Fac'], ramp.inputs[0])
        links.new(ramp.outputs[0], bsdf.inputs['Base Color'])
        if bump:
            relief = nodes.new('ShaderNodeBump')
            relief.inputs['Strength'].default_value = .32
            relief.inputs['Distance'].default_value = bump
            links.new(tex.outputs['Fac'], relief.inputs['Height'])
            links.new(relief.outputs[0], bsdf.inputs['Normal'])
    return material

# Wardrobe, groom, and performance adaptation. Face base is Blender Studio's
# Einar rig, CC BY 4.0, Blender Foundation | studio.blender.org.
with bpy.data.libraries.load(str(ASSETS / 'einar.blend'), link=False) as (_, library):
    library.collections = ['CH-einar']
cast = library.collections[0]
cast.name = 'Performance • The field keeper'
scene.collection.children.link(cast)
rig = bpy.data.objects['RIG-einar']
rig.name = 'Field keeper • Face and body controls'
for obj in cast.all_objects:
    if obj.type in {'MESH', 'CURVES', 'ARMATURE', 'LATTICE', 'EMPTY'} and obj.parent is None and not obj.name.startswith('WGT-'):
        obj.location.z -= .657
    if obj.type in {'LIGHT', 'CAMERA'} or obj.name.startswith('WGT-'):
        obj.hide_render = True
bpy.data.objects['GEO-einar_hat'].hide_render = True
for name, mat in {
    'einar.jacket.canvas': surface('Petrol blue • weathered waxed cotton', (.012,.045,.050), (.065,.142,.151), 155, .82, .0016),
    'einar.jacket.collar': surface('Faded slate • jacket facing', (.029,.052,.055), (.095,.145,.144), 225, .9, .0012),
    'einar.jacket.rim': surface('Slate • stitched binding', (.041,.076,.082)),
    'einar.sweater': surface('Ochre wool • collar', (.091,.039,.014), (.24,.116,.044), 265, .95, .0018),
}.items():
    source = bpy.data.materials.get(name)
    if source:
        source.user_remap(mat)

# Salt-and-pepper auburn strands give the keeper a distinct outdoor look.
strand = surface('Auburn and silver • field keeper groom', (.072,.027,.012), rough=.49)
nodes, links = strand.node_tree.nodes, strand.node_tree.links
info = nodes.new('ShaderNodeHairInfo')
palette = nodes.new('ShaderNodeValToRGB')
palette.color_ramp.elements.remove(palette.color_ramp.elements[1])
palette.color_ramp.elements[0].color = (.021,.011,.008,1)
for threshold, rgb in [(.51,(.06,.027,.014)),(.78,(.115,.058,.029)),
                       (.88,(.19,.145,.104)),(.98,(.32,.30,.26))]:
    palette.color_ramp.elements.new(threshold).color = (*rgb,1)
links.new(info.outputs['Random'],palette.inputs[0])
links.new(palette.outputs[0],nodes.get('Principled BSDF').inputs['Base Color'])
for obj in cast.all_objects:
    if obj.type == 'CURVES' and any(part in obj.name for part in ('hair','beard','mustache')):
        for index in range(len(obj.data.materials)):
            obj.data.materials[index] = strand

bones = rig.pose.bones

def pose(name, prop, keys):
    bone = bones[name]
    if prop == 'rotation_euler':
        bone.rotation_mode = 'XYZ'
    for frame, values in keys:
        setattr(bone, prop, values)
        bone.keyframe_insert(data_path=prop, frame=frame, group=name)

def y_keys(name, keys):
    pose(name, 'location', [(f, (0, y, 0)) for f, y in keys])

# World metres, 12 fps. The back of the jacket rests on the oak while the
# torso expands about its seated base. The head/gaze timing is deliberate.
pose('MSTR-Spine_Torso', 'rotation_euler', [(f,(radians(a),0,0)) for f,a in
     [(1,-.20),(9,-.49),(18,-.18),(27,-.05),(36,-.48),(48,-.18)]])
pose('FK-Head', 'rotation_euler', [(f,tuple(map(radians,(p,y,r)))) for f,p,y,r in
     [(1,-1,-2,2),(14,-1,-2,2),(19,-.8,-1.7,2),(25,-.4,3.8,1.5),
      (31,2,6,1.1),(38,3.3,6.7,1),(48,3.1,6.5,1)]])
pose('MSTR-TGT-Eyes', 'location', [(1,(-.06,0,.014)),(13,(-.06,0,.014)),
     (16,(-.225,0,.125)),(20,(-.29,0,.052)),(25,(-.27,0,-.059)),
     (30,(-.24,0,-.153)),(33,(-.21,0,-.19)),(38,(-.15,0,-.121)),
     (48,(-.145,0,-.112))])
for side, factor in [('L',1),('R',.76)]:
    y_keys('ACT-Eyebrow_Inner.'+side, [(1,-.0028*factor),(14,-.0028*factor),
           (22,-.0018*factor),(32,-.0018*factor),(43,-.0009*factor),(48,-.0009*factor)])
    y_keys('ACT-Eyebrow_Outer.'+side, [(1,.0009*factor),(17,.0009*factor),
           (23,.0016*factor),(36,.001*factor),(48,.0007*factor)])
    y_keys('Blink.'+side, [(1,0),(34,0),(35,-.0034),(36,-.006),(37,-.0027),(38,0),(48,0)])
    sign = -1 if side == 'L' else 1
    pose('ACT-Mouth_Corner.'+side, 'location', [(1,(sign*.0017,.0014,0)),
          (34,(sign*.0017,.0014,0)),(40,(0,.0003,0)),(48,(0,.0003,0))])

def point_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z','Y').to_euler()

cam_data = bpy.data.cameras.new('48 mm • three-quarter portrait')
camera = bpy.data.objects.new('Locked portrait camera', cam_data)
shot_col.objects.link(camera)
camera.location = (.312,-.867,.993)
point_at(camera, (.041,-.060,.934))
cam_data.lens = 46
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = .807
cam_data.dof.aperture_fstop = 4.0
scene.camera = camera
bpy.context.view_layer.update()

def lamp(name, kind, location, target, power, color, size):
    data = bpy.data.lights.new(name, kind)
    obj = bpy.data.objects.new(name, data)
    shot_col.objects.link(obj)
    obj.location = location
    point_at(obj, target)
    data.energy, data.color = power, color
    if kind == 'AREA':
        data.size = size
        data.use_shadow = False
    else:
        data.angle = size
    return obj

lamp('Sun • late afternoon across the field','SUN',(1.9,3.6,3.1),(0,0,1),2.05,(1,.71,.42),.16)
lamp('Open sky • soft face and catchlights','AREA',(.38,-1.65,2.2),(0,-.06,1),91,(.82,.9,1),2.25)
lamp('Warm bounce from dry meadow','AREA',(1.1,-.36,.48),(0,0,1),16,(1,.74,.53),1.22)
lamp('Cool shade • camera left','AREA',(-1.15,-.43,1.28),(0,0,1),13,(.63,.77,1),1.45)

world = bpy.data.worlds.new('Soft blue sky above a warm horizon')
scene.world = world
world.use_nodes = True
nodes, links = world.node_tree.nodes, world.node_tree.links
bg = nodes.get('Background')
bg.inputs['Strength'].default_value = .52
sky = nodes.new('ShaderNodeTexCoord')
axis = nodes.new('ShaderNodeSeparateXYZ')
links.new(sky.outputs['Normal'], axis.inputs[0])
gradient = nodes.new('ShaderNodeMapRange')
gradient.inputs['From Min'].default_value = -.37
gradient.inputs['From Max'].default_value = .06
links.new(axis.outputs['Z'], gradient.inputs['Value'])
colors = nodes.new('ShaderNodeValToRGB')
colors.color_ramp.elements[0].color = (.32,.53,.70,1)
colors.color_ramp.elements[1].color = (.79,.79,.62,1)
links.new(gradient.outputs[0], colors.inputs[0])
links.new(colors.outputs[0], bg.inputs[0])

# Bark longitudinal UVs wrap an irregular, gently leaning support.
bark = surface('Oak • furrowed bark', (.15,.10,.064), rough=.88)
nodes, links = bark.node_tree.nodes, bark.node_tree.links
shader = nodes.get('Principled BSDF')
for filename, socket in [('oak_bark_diffuse.jpg','Base Color'),('oak_bark_normal.jpg','Normal')]:
    node = nodes.new('ShaderNodeTexImage')
    node.image = bpy.data.images.load(str(ASSETS / 'environment' / filename))
    node.image.pack()
    if socket == 'Normal':
        node.image.colorspace_settings.name = 'Non-Color'
        normal = nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value = 1.18
        links.new(node.outputs[0], normal.inputs['Color'])
        links.new(normal.outputs[0], shader.inputs[socket])
    else:
        links.new(node.outputs[0], shader.inputs[socket])
verts, faces = [], []
sides, levels = 96, 66
for j in range(levels):
    z = -.16 + j*.057
    for i in range(sides):
        a = 2*pi*i/sides
        radius = (.362 - .027*z + .15*exp(-max(z,0)*11)
                  + .012*sin(a*8 + z*2) + .009*sin(a*17 - z*4))
        verts.append((-.252 -.07*(z-1) + radius*cos(a), .337 + .022*z + radius*sin(a), z))
for j in range(levels-1):
    for i in range(sides):
        a = j*sides+i
        b = j*sides+(i+1)%sides
        faces.append((a,b,b+sides,a+sides))
trunk = mesh('Mature oak • trunk at the shoulder', verts, faces, set_col, [bark])
uv = trunk.data.uv_layers.new(name='Bark wrap')
for poly in trunk.data.polygons:
    poly.use_smooth = True
    i, j = poly.index % sides, poly.index // sides
    for idx, (u,v) in zip(poly.loop_indices, [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]):
        uv.data[idx].uv = (u/sides*2.55,v*.057*1.24)

def ground_height(x,y):
    return .64*(1-exp(-max(y,0)/4.1)) + .05*sin(x*.29+y*.47)*(1-exp(-max(y,0)))

earth = surface('Meadow • olive and dry straw', (.073,.095,.023), (.32,.285,.084), 1.7, .93, .024)
verts, faces = [], []
width = 121
for j in range(126):
    y = j*.42-4
    for i in range(width):
        x = (i-60)*.42
        verts.append((x,y,ground_height(x,y)))
for j in range(125):
    for i in range(width-1):
        a = j*width+i
        faces.append((a,a+1,a+1+width,a+width))
ground = mesh('Meadow rise', verts, faces, set_col, [earth])
for poly in ground.data.polygons:
    poly.use_smooth = True

def plant_material(name, low, high):
    mat = surface(name, low, high, 5.0, .81)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get('Principled BSDF')
    translucency = nodes.new('ShaderNodeBsdfTranslucent')
    links.new(nodes.get('Color Ramp').outputs[0], translucency.inputs['Color'])
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = .24
    links.new(shader.outputs[0], mix.inputs[1])
    links.new(translucency.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], nodes.get('Material Output').inputs[0])
    return mat

plant_mats = [
    plant_material('Grass • sage', (.075,.115,.025), (.25,.32,.064)),
    plant_material('Grass • late summer olive', (.108,.135,.035), (.35,.37,.071)),
    plant_material('Dry bent grass', (.22,.155,.047), (.52,.37,.118)),
    plant_material('Dry oat seed heads', (.23,.125,.032), (.58,.375,.104)),
    plant_material('Field sorrel', (.08,.115,.029), (.28,.35,.072)),
]

# Roots remain fixed. Each patch is sampled as a damped cantilever driven by
# a traveling gust. Shelter weakens the force close to the trunk.
# Coherent plant response reference: https://doi.org/10.1017/S0022112010001746
# The patch delay and stiffness are visual estimates for this shot.
def gust(t):
    rise = max(0, min(1, (t-1.00)/.53))
    fall = max(0, min(1, (2.68-t)/.59))
    return (rise*rise*(3-2*rise))*(fall*fall*(3-2*fall))

def meadow_patch(x, y, index):
    verts, faces, indices, bends = [], [], [], []
    for _ in range(44):
        dx, dy = RNG.uniform(-.42,.42), RNG.uniform(-.38,.38)
        root = Vector((dx,dy,ground_height(x+dx,y+dy)))
        for blade in range(RNG.randint(4,7)):
            angle = RNG.uniform(0,2*pi)
            side = Vector((cos(angle),sin(angle),0))
            out = Vector((-side.y,side.x,0))
            h = RNG.uniform(.09,.39)
            broad = RNG.random() < .075
            w = RNG.uniform(.007,.018) if not broad else RNG.uniform(.025,.045)
            lean = RNG.uniform(.12,.73)*h
            start = len(verts)
            mat = 4 if broad else RNG.choices([0,1,2],[5,5,2])[0]
            for k in range(6):
                t = k/5
                center = root + out*(lean*t*t) + Vector((0,0,h*(t-.12*t**3)))
                half = w*.5*(1-t**1.6)
                for direction in [-1,1]:
                    verts.append(center+side*direction*half)
                    bends.append(h*t*t)
                if k:
                    a = start+2*k
                    faces.append((a-2,a-1,a+1,a))
                    indices.append(mat)
            if blade == 0 and h > .23:
                center = root + out*lean + Vector((0,0,h*.88))
                for seed in range(5):
                    p = center + Vector((0,0,seed*.012))
                    half = .0065*(1-seed*.1)
                    a = len(verts)
                    verts.extend([p+side*half,p+out*half,p-side*half,p-out*half,
                                  p+Vector((0,0,.017))])
                    bends.extend([h+seed*.012]*5)
                    for j in range(4):
                        faces.append((a+j,a+(j+1)%4,a+4))
                        indices.append(3)
    obj = mesh('Rooted meadow patch %02d'%index, verts, faces, wind_col, plant_mats)
    obj.location = (x,y,0)
    for poly, mat in zip(obj.data.polygons, indices):
        poly.material_index = mat
        poly.use_smooth = True
    obj.shape_key_add(name='Rest')
    bend = obj.shape_key_add(name='Gust flex')
    bend.slider_min = -.4
    coordinates = array('f', (value for co, amount in zip(verts,bends)
                               for value in (co[0]+.66*amount, co[1]+.26*amount, co[2]-.145*amount)))
    bend.data.foreach_set('co',coordinates)
    delay = (x+4)*.075 + (y-3)*.054
    shelter = min(1,max(.23,(x+.24*y+1.25)/1.65))
    displacement, speed = 0., 0.
    dt = 1/120
    for tick in range(471):
        t = tick*dt-delay
        driving = .71*gust(t)*(1+.24*sin(13*t+y*1.26))
        driving += .034*sin(3*t+y)
        speed += (114*(driving-displacement)-8.8*speed)*dt
        displacement += speed*dt
        if tick%10 == 0:
            bend.value = displacement*shelter
            bend.keyframe_insert(data_path='value', frame=1+tick//10)

index = 0
for j in range(11):
    y = 2.2+j*.65
    center_x = camera.location.x - .31*(y+.86)
    for i in range(10):
        x = center_x+(i-4.0)*.72+RNG.uniform(-.16,.16)
        meadow_patch(x,y+RNG.uniform(-.15,.15),index)
        index += 1

# Irregular distant windbreak beyond the exposed meadow.
canopy = [
    surface('Windbreak • olive shadow', (.051,.074,.022), (.19,.22,.057), 2.2),
    surface('Windbreak • autumn olive', (.098,.111,.028), (.265,.24,.065), 2.2),
    surface('Windbreak • copper', (.13,.068,.022), (.36,.22,.062), 2.2),
]
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2)
prototype = bpy.context.object
crown = prototype.data
bpy.data.objects.remove(prototype, do_unlink=True)
for material in canopy:
    crown.materials.append(material)
for poly in crown.polygons:
    poly.use_smooth = True
    poly.material_index = RNG.choices([0,1,2],[7,5,1])[0]
for i in range(42):
    x, y = -19+i*.64, RNG.uniform(15,22)
    h = RNG.uniform(.8,1.55)
    for k in range(4):
        obj = bpy.data.objects.new('Distant hedgerow',crown)
        set_col.objects.link(obj)
        obj.location = (x+RNG.uniform(-.6,.6),y+RNG.uniform(-.45,.45),h+RNG.uniform(-.28,.26))
        obj.scale = (RNG.uniform(.67,1.2),RNG.uniform(.66,1.08),RNG.uniform(.52,.97))

leaf_mats = [
    plant_material('Oak leaf • amber', (.23,.063,.009), (.72,.30,.039)),
    plant_material('Oak leaf • russet', (.15,.032,.008), (.49,.143,.018)),
    plant_material('Oak leaf • old gold', (.29,.12,.016), (.64,.42,.076)),
    surface('Oak veins • muted straw', (.35,.173,.047), rough=.82),
]

def oak_leaf(name, length, material):
    verts, faces = [], []
    profiles = [.045,.23,.34,.285,.46,.35,.49,.39,.43,.24,.30,.15,0]
    for i, width in enumerate(profiles):
        t = i/(len(profiles)-1)
        y = (t-.44)*length
        for j in range(5):
            u = (j-2)/2
            x = length*(u*width*.60+ .046*sin(t*3.6))
            z = length*(.21*u*u*width+.13*(t-.47)**2+.027*u*sin(t*8))
            verts.append((x,y,z))
            if i and j:
                a = i*5+j
                faces.append((a-6,a-5,a,a-1))
    obj = mesh(name, verts, faces, leaf_col, [leaf_mats[material]])
    for poly in obj.data.polygons:
        poly.use_smooth = True
    curve = bpy.data.curves.new(name+' • stem and veins','CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = length*.009
    curve.bevel_resolution = 1
    curve.materials.append(leaf_mats[-1])
    lines = [[(0,-.60*length,0), *[verts[5*i+2] for i in range(12)]]]
    for i in [1,3,5,7,9]:
        lines.extend([[verts[5*i+2],verts[5*(i+1)+j]] for j in (0,4)])
    for points in lines:
        line = curve.splines.new('POLY')
        line.points.add(len(points)-1)
        for point, xyz in zip(line.points,points):
            point.co = (*xyz,1)
    veins = bpy.data.objects.new(curve.name,curve)
    leaf_col.objects.link(veins)
    veins.parent = obj
    veins.location.z = .0004
    return obj

def at_camera(u,v,depth):
    w = depth*cam_data.sensor_width/cam_data.lens
    h = w*scene.render.resolution_y/scene.render.resolution_x
    return camera.matrix_world @ Vector(((u-.5)*w,(v-.5)*h,-depth))

# Pre-baked drag and gravity proxy with a 120 Hz fixed step. The leaves are
# attached above frame until release, with continuous pose and zero initial
# velocity. Terminal speeds, airflow, and roll are shot-scale estimates.
# Alternating lateral lift and changing drag approximate the observed flutter
# and tumble modes of falling plates (Andersen, Pesavento & Wang, JFM 2005).
# https://dragonfly.tam.cornell.edu/publications/2005_JFM_Andersen_Pesavento_Wang_a.pdf
def falling_leaf(name, start, u, depth, size, terminal, phase, material, turn):
    obj = oak_leaf(name,size,material)
    position = at_camera(u,1.10,depth)
    velocity = Vector((0,0,0))
    right = camera.matrix_world.to_3x3().col[0]
    dt = 1/120
    settled = False
    for tick in range(471):
        t = tick*dt
        age = max(t-start,0)
        if not settled:
            spin_time = age - .10*(1-exp(-age/.10))
            roll = phase + turn*spin_time + .63*sin(spin_time*7+phase)*min(spin_time*6,1)
            rotation = (1.06+.51*sin(roll), roll, .27+spin_time*.46+.46*sin(spin_time*7+phase))
        if age and not settled:
            flow = right*(.018+.12*gust(t)+.025*sin(age*6+phase))
            relative = velocity-flow
            drag = 9.81/(terminal*terminal)*(.83+.29*abs(cos(roll)))
            accel = Vector((0,0,-9.81))-relative*(drag*relative.length)
            accel += right*(1.65*sin(11*age+phase))
            velocity += accel*dt
            position += velocity*dt
            floor = ground_height(position.x, position.y)+.012
            if position.z < floor:
                position.z = floor
                settled = True
        if tick%10 == 0:
            obj.location = position
            obj.rotation_euler = rotation
            obj.keyframe_insert(data_path='location',frame=1+tick//10)
            obj.keyframe_insert(data_path='rotation_euler',frame=1+tick//10)

falling_leaf('01 • leaf caught by his gaze',1.04,.687,.74,.062,.34,.8,0,1.1)
falling_leaf('02 • copper leaf behind',1.23,.828,1.81,.082,.56,2.2,1,2.4)
falling_leaf('03 • high distant leaf',1.51,.888,3.35,.093,.48,3.4,2,3.1)
falling_leaf('04 • russet leaf in the lull',2.25,.727,1.38,.052,.41,1.7,1,2.5)
falling_leaf('05 • last pale leaf',2.80,.828,2.22,.079,.42,4.1,2,1.9)

for frame, label in [(1,'Watching'),(13,'Gust reaches the meadow'),(16,'Eyes find the leaf'),
                     (21,'Head follows'),(32,'Gust recedes'),(36,'Blink'),(43,'Hold')]:
    scene.timeline_markers.new(label,frame=frame)
scene['asset_credit'] = 'Adapted from Einar Rig (CC BY 4.0), Blender Foundation | studio.blender.org. Bark maps by Charlotte Baglioni, Poly Haven (CC0).'
scene.frame_set(1)
