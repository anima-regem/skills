import bpy
import math
import random
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, 48
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.view_settings.view_transform = 'AgX'
rng = random.Random(421)

def material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return mat

grass = material('Dry sage meadow', (.29, .34, .15))
sand = material('Ochre exposed bank', (.41, .25, .125))
silt = material('Damp sand', (.23, .16, .093))
stones = [material('River stone %s' % i, c) for i, c in enumerate(
    [(.22,.26,.23), (.35,.35,.27), (.30,.32,.29), (.45,.40,.30)])]
blades = [material('Grass %s' % i, c) for i, c in enumerate(
    [(.39,.41,.16), (.52,.48,.19), (.22,.29,.13)])]
foam = [material('Water trace %s' % i, c, .42) for i, c in enumerate(
    [(.20,.50,.49), (.36,.65,.61), (.57,.78,.68)])]
leaf = material('Floating amber leaves', (.93,.39,.066))
coat = material('Vermilion canvas', (.58,.103,.040))
collar = material('Canvas binding', (.34,.056,.027))
pants = material('Indigo trousers', (.043,.075,.097))
boot = material('Leather boots', (.064,.040,.030))
sole = material('Boot soles', (.028,.028,.023))
skin = material('Warm brown skin', (.51,.242,.13))
hair = material('Dark hair', (.065,.031,.020))
cap = material('Honey wool cap', (.88,.47,.083))
cuff = material('Knitted cap band', (.69,.295,.042))

def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj

def ball(name, pos, scale, mat, ico=False):
    if ico:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, location=pos)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    if not ico:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj

def shore(x, side):
    return side * (2.12 + .18 * math.sin(x*.43 + side) + .12*math.sin(x*.78))

# Each cross section runs from the wet margin up through exposed sand to meadow.
sections = [(-.10,-.105), (.10,.035), (.34,.085), (.53,.37),
            (.86,.52), (1.31,.55), (2.45,.57), (5,.60), (15,.65)]
for side in [-1, 1]:
    verts = [(x, shore(x,side)+side*d,
              z + .035*math.sin(1.4*x+side)*min(d+.1,1))
             for x in [i*.25 for i in range(-112,113)] for d,z in sections]
    n = len(sections)
    faces = [(i*n+j, (i+1)*n+j, (i+1)*n+j+1, i*n+j+1)
             for i in range(224) for j in range(n-1)]
    if side < 0:
        faces = [face[::-1] for face in faces]
    bank = mesh('Near bank' if side < 0 else 'Far bank', verts, faces, silt)
    for mat in [sand, grass]:
        bank.data.materials.append(mat)
    for poly in bank.data.polygons:
        poly.material_index = [0,0,1,1,2,2,2,2][poly.index % (n-1)]
        poly.use_smooth = True

water = material('Jade water', (.045,.29,.29), .31)
nodes = water.node_tree.nodes
links = water.node_tree.links
geo = nodes.new('ShaderNodeTexCoord')
shift = nodes.new('ShaderNodeVectorMath')
shift.operation = 'ADD'
shift.inputs[1].default_value = (0,0,0)
shift.inputs[1].keyframe_insert('default_value', frame=1)
shift.inputs[1].default_value = (-5.6,0,0)
shift.inputs[1].keyframe_insert('default_value', frame=48)
links.new(geo.outputs['Object'], shift.inputs[0])
stretch = nodes.new('ShaderNodeVectorMath')
stretch.operation = 'MULTIPLY'
stretch.inputs[1].default_value = (.92,4.7,1)
links.new(shift.outputs[0], stretch.inputs[0])
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.9
noise.inputs['Detail'].default_value = 2
links.new(stretch.outputs[0], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .22
ramp.color_ramp.elements[0].color = (.028,.155,.16,1)
ramp.color_ramp.elements[1].position = .82
ramp.color_ramp.elements[1].color = (.108,.396,.387,1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
shader = nodes.get('Principled BSDF')
links.new(ramp.outputs[0], shader.inputs['Base Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .19
bump.inputs['Distance'].default_value = .038
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs[0], shader.inputs['Normal'])
mesh('Water surface', [(-28,-3,0),(28,-3,0),(28,3,0),(-28,3,0)],
     [(0,1,2,3)], water)

def linear(owner):
    anim = owner.animation_data
    for layer in anim.action.layers:
        for strip in layer.strips:
            for curve in strip.channelbag(anim.action_slot).fcurves:
                for key in curve.keyframe_points:
                    key.interpolation = 'LINEAR'

linear(water.node_tree)

def ribbon(name, length, width, bend, mat):
    verts = []
    for i in range(9):
        t = i/8
        y = bend*math.sin(math.pi*t)
        taper = width*(.04+.96*math.sin(math.pi*t)**.75)
        verts.extend([(length*t,y-taper,0),(length*t,y+taper,0)])
    return mesh(name, verts, [(i,i+2,i+3,i+1) for i in range(0,16,2)], mat)

for i in range(95):
    x, y = rng.uniform(-22,16), rng.uniform(-1.93,1.93)
    length = rng.uniform(.24,1.38)
    trace = ribbon('Advecting surface glint', length, rng.uniform(.009,.026),
                   rng.uniform(-.065,.065), rng.choices(foam,[8,3,1])[0])
    trace.location = (x,y,.013)
    trace.keyframe_insert('location', frame=1)
    trace.location.x += 2.45+3.4*(1-(y/2.2)**2)
    trace.keyframe_insert('location', frame=48)
    linear(trace)

# A few recognizable leaves make the current's direction apparent at a glance.
for x, y, phase in [(-5.6,-.92,0),(-2.9,-.55,1),(-1.75,-.68,2),
                    (2.0,.6,3),(-7.7,1.1,4)]:
    floater = ball('Drifting willow leaf', (x,y,.041), (.127,.061,.016), leaf)
    speed = 2.45+3.4*(1-(y/2.2)**2)
    for f in [1, 12, 24, 36, 48]:
        t = (f-1)/47
        floater.location = (x+speed*t,y+.055*math.sin(t*6+phase),.04)
        floater.rotation_euler.z = .40*math.sin(t*8+phase)
        floater.keyframe_insert('location', frame=f)
        floater.keyframe_insert('rotation_euler', frame=f)
    linear(floater)

for x,y,sz in [(-5.05,.99,.48),(3.50,-1.14,.36),(4.12,-1.30,.19),
               (6.48,1.55,.31),(-5.55,1.23,.21)]:
    rock = ball('Current-worn rock', (x,y,.025),(sz,sz*.74,sz*.69),stones[0],True)
    rock.rotation_euler.z = rng.uniform(-1,1)
    for sign in [-1,1]:
        for j in range(2):
            wake = ribbon('Rock wake', sz*(2.8+j*.8), .018-j*.004,
                          -sign*sz*.18, foam[1-j])
            wake.location = (x-sz*.53+j*.19,y+sign*sz*(.47+j*.25),.018+j*.001)
            wake.rotation_euler.z = sign*(.12+j*.055)

# Bank scatter is deterministic and leaves open space around the watcher.
for i in range(145):
    x = rng.uniform(-16,16)
    side = rng.choice([-1,1])
    d = rng.uniform(.16,2.8)
    y = shore(x,side)+side*d
    if side == -1 and -4.05 < x < -1.25 and d < 1.8:
        continue
    if d < .55 or rng.random() < .24:
        size = rng.uniform(.055,.22)
        level = .07 if d < .36 else (.36 if d < .54 else .54)
        ball('Bank pebble',(x,y,level),(size,size*.71,size*.56),rng.choice(stones),True)
        continue
    verts, faces = [], []
    for j in range(rng.randint(4,9)):
        dx,dy = rng.uniform(-.13,.13),rng.uniform(-.13,.13)
        h = rng.uniform(.15,.43)
        bend = rng.uniform(-.12,.17)
        k = len(verts)
        verts.extend([(x+dx-.024,y+dy,.48),(x+dx+.024,y+dy,.48),
                      (x+dx+bend*.35+.018,y+dy+.024,.53+h*.48),
                      (x+dx+bend*.35-.018,y+dy+.024,.53+h*.48),
                      (x+dx+bend,y+dy+.045,.53+h)])
        faces.extend([(k,k+1,k+2,k+3),(k+3,k+2,k+4)])
    mesh('Tuft of sedge',verts,faces,rng.choice(blades))

# Build a compact seated silhouette in local coordinates, with +Y forward.
x0 = -2.55
y0 = shore(x0,-1)-.99
yaw = -.65
origin = Vector((x0,y0,0))

def world(p):
    x,y,z = p
    return origin + Vector((x*math.cos(yaw)-y*math.sin(yaw),
                            x*math.sin(yaw)+y*math.cos(yaw),z))

def part(name, pos, scale, mat):
    obj = ball(name, world(pos), scale, mat)
    obj.rotation_euler.z = yaw
    return obj

def limb(name, a, b, widths, mat):
    a,b = world(a),world(b)
    obj = ball(name, (a+b)*.5, (*widths,(b-a).length*.5+widths[1]*.55), mat)
    obj.rotation_euler = (b-a).to_track_quat('Z','Y').to_euler()
    return obj

seat = ball('Broad seat stone',world((0,-.10,.59)),(.64,.48,.39),stones[2],True)
seat.rotation_euler.z = yaw
part('Hips',(0,0,1.02),(.286,.214,.185),pants)
limb('Jacket body',(0,-.04,1.13),(0,.125,1.64),(.294,.204),coat)
part('Jacket hem',(0,-.03,1.12),(.292,.219,.085),collar)
part('Collar',(0,.146,1.67),(.154,.132,.072),collar)
part('Neck',(0,.17,1.715),(.097,.085,.103),skin)
for side in [-1,1]:
    a = (side*.168,.035,1.045)
    knee = (side*.231,.51,.99 + side*.03)
    ankle = (side*.256,.41,.45 + side*.13)
    limb('Thigh',a,knee,(.136,.135),pants)
    limb('Shin',knee,ankle,(.103,.106),pants)
    bx,by,bz = ankle
    part('Boot',(bx,by+.074,bz-.019),(.116,.198,.091),boot)
    part('Outsole',(bx,by+.079,bz-.084),(.122,.203,.032),sole)
    shoulder = (side*.24,.125,1.575)
    elbow = (side*.318,.29,1.28)
    wrist = (side*.237,.46,1.122 + side*.03)
    limb('Upper sleeve',shoulder,elbow,(.103,.105),coat)
    limb('Forearm',elbow,wrist,(.088,.085),coat)
    limb('Cuff',Vector(wrist)*.86+Vector(elbow)*.14,wrist,(.077,.07),collar)
    part('Hand',(wrist[0],wrist[1]+.046,wrist[2]-.024),(.068,.109,.050),skin)

head = bpy.data.objects.new('Watch the leaf pass',None)
scene.collection.objects.link(head)
head.location = world((0,.173,1.74))
head.rotation_mode = 'XYZ'

def head_part(name, pos, scale, mat):
    obj = ball(name,pos,scale,mat)
    obj.parent = head
    return obj

head_part('Face',(0,.019,.129),(.155,.14,.188),skin)
head_part('Hair at nape',(0,-.053,.152),(.158,.099,.158),hair)
head_part('Nose',(0,.149,.111),(.047,.045,.035),skin)
for side in [-1,1]:
    head_part('Ear',(side*.143,.015,.111),(.035,.038,.051),skin)
    head_part('Eye',(side*.084,.137,.141),(.019,.014,.012),hair)
    brow = head_part('Brow',(side*.084,.127,.166),(.027,.011,.008),hair)
    brow.rotation_euler.y = side*.14
head_part('Wool hat',(0,-.025,.251),(.164,.151,.110),cap)
head_part('Folded brim',(0,-.019,.216),(.168,.155,.054),cuff)

for f,z,tilt in [(1,.39,-.18),(13,.18,-.22),(26,-.13,-.26),
                 (38,-.46,-.21),(48,-.58,-.15)]:
    head.rotation_euler = (tilt, .02, yaw+z)
    head.keyframe_insert('rotation_euler', frame=f)

# A little distant vegetation anchors the opposite shore without obscuring it.
bark = material('Willow bark',(.22,.145,.082))
canopy = [material('Autumn willow %s'%i,c) for i,c in enumerate(
    [(.43,.38,.12),(.58,.47,.15),(.32,.34,.13)])]
for x,y,h in [(-8.5,4.06,1.84),(-7.48,4.45,1.33),(6.25,4.8,1.75),(7.9,4.85,1.96)]:
    start = Vector((x,y,.55))
    tip = Vector((x+.14,y,h+.55))
    trunk = ball('Willow trunk',(start+tip)*.5,(.076,.087,h*.57),bark,True)
    trunk.rotation_euler = (tip-start).to_track_quat('Z','Y').to_euler()
    for i in range(8):
        r = rng.uniform(.25,.49)
        ball('Loose willow crown',(tip.x+rng.uniform(-.53,.53),
             y+rng.uniform(-.40,.40),tip.z+rng.uniform(-.34,.45)),
             (r,r*.85,r*1.22),rng.choice(canopy),True)

world_bg = bpy.data.worlds.new('Soft pale sky')
scene.world = world_bg
world_bg.use_nodes = True
world_bg.node_tree.nodes['Background'].inputs[0].default_value = (.49,.66,.78,1)
world_bg.node_tree.nodes['Background'].inputs[1].default_value = .53

def light(name, kind, pos, target, power, color):
    data = bpy.data.lights.new(name,kind)
    data.energy = power
    data.color = color
    obj = bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    return data

light('Late sun','SUN',(-5,-3,8),(0,0,0),2.4,(1,.83,.62)).angle = .13
light('Open sky fill','AREA',(2,-5,8),(0,0,0),480,(.66,.83,1)).size = 8
camera = bpy.data.objects.new('Riverbank camera',bpy.data.cameras.new('Riverbank camera'))
scene.collection.objects.link(camera)
camera.location = (4.35,-11.8,7.9)
target = Vector((-.42,-.34,.57))
camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 10.8
scene.camera = camera
scene.frame_set(1)
