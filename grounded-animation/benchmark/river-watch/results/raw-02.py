import math
import random

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
rng = random.Random(21)
scene.frame_start, scene.frame_end = 1, 48
scene.render.fps = 12
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'


def material(name, color, roughness=.75):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    shader = m.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return m


turf = material('Sage felt', (.31, .39, .19))
far_turf = material('Olive felt', (.22, .34, .22))
earth = material('Exposed ochre clay', (.36, .24, .125))
sand = material('Wet ochre at the waterline', (.46, .34, .185))
stones = [material('Riverstone %s' % i, c) for i, c in enumerate([
    (.22, .27, .25), (.34, .35, .29), (.43, .40, .31)])]
leaves = [material('Sedge %s' % i, c) for i, c in enumerate([
    (.24, .33, .12), (.38, .44, .17), (.54, .49, .21)])]
jacket = material('Marigold anorak', (.82, .285, .035))
seam = material('Anorak seams', (.56, .15, .025))
hood = material('Golden hood', (.95, .405, .055))
pants = material('Blue charcoal trousers', (.065, .107, .125))
boots = material('Umber boots', (.105, .061, .042))
soles = material('Boot soles', (.052, .036, .030))
skin = material('Warm terracotta skin', (.51, .237, .126))
hair = material('Dark brown hair', (.055, .028, .021))
eyes = material('Dark eyes', (.025, .016, .013))


def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def oval(name, position, scale, mat, parent=None, ico=False):
    if ico:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16)
    ob = bpy.context.object
    ob.name = name
    ob.parent = parent
    ob.location = position
    ob.scale = scale
    ob.data.materials.append(mat)
    if not ico:
        for face in ob.data.polygons:
            face.use_smooth = True
    return ob


def limb(name, start, end, width, depth, mat, parent):
    a, b = Vector(start), Vector(end)
    ob = oval(name, (a+b)/2, (width, depth, (b-a).length/2 + width*.72), mat, parent)
    ob.rotation_euler = (b-a).to_track_quat('Z','Y').to_euler()
    return ob


def channel(x):
    return .40*math.sin(.34*x+.4) + .17*math.sin(.72*x)


def edge(x, side):
    return channel(x) + side*(2.65+.19*math.sin(.42*x + side))


xs = [i*.30 for i in range(-75, 76)]
for side in (-1, 1):
    profile = [(-.30,-.20), (.0,.013), (.17,.085), (.36,.22),
               (.65,.32), (1.15,.39), (2.20,.43), (3.50,.48), (12,.47)]
    verts = []
    for x in xs:
        for d, z in profile:
            amount = min(1, max(0, d)*1.8)
            verts.append((x, edge(x, side)+d*side,
                          z+amount*(.023*math.sin(x*1.5+d)+.018*math.cos(x*.8+d*2))))
    count = len(profile)
    faces = [(i*count+j, (i+1)*count+j, (i+1)*count+j+1, i*count+j+1)
             for i in range(len(xs)-1) for j in range(count-1)]
    if side == -1:
        faces = [tuple(reversed(f)) for f in faces]
    bank = mesh('Near bank' if side < 0 else 'Far bank', verts, faces, sand)
    bank.data.materials.append(earth)
    bank.data.materials.append(turf if side < 0 else far_turf)
    for poly in bank.data.polygons:
        j = poly.index % (count-1)
        poly.material_index = 0 if j < 2 else 1 if j == 2 else 2
        poly.use_smooth = True

water = material('Moving turquoise water', (.028,.28,.29), .28)
nt = water.node_tree
nodes = nt.nodes
link = nt.links.new
tex = nodes.new('ShaderNodeTexCoord')
moving = nodes.new('ShaderNodeVectorMath')
moving.operation = 'ADD'
link(tex.outputs['Object'], moving.inputs[0])
for frame, offset in [(1,0), (48,-5.0)]:
    moving.inputs[1].default_value = (offset,0,0)
    moving.inputs[1].keyframe_insert(data_path='default_value', frame=frame)
scale = nodes.new('ShaderNodeVectorMath')
scale.operation = 'MULTIPLY'
scale.inputs[1].default_value = (.57, 4.2, 1)
link(moving.outputs[0],scale.inputs[0])
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.65
noise.inputs['Detail'].default_value = 2.2
link(scale.outputs[0],noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
for idx, (p,c) in enumerate([
    (.19,(.012,.15,.185,1)), (.52,(.022,.33,.35,1)), (.77,(.125,.49,.46,1))]):
    elt = ramp.color_ramp.elements[0] if idx == 0 else ramp.color_ramp.elements.new(p)
    elt.position, elt.color = p,c
link(noise.outputs['Fac'],ramp.inputs[0])
bsdf = nodes.get('Principled BSDF')
link(ramp.outputs[0],bsdf.inputs['Base Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .22
bump.inputs['Distance'].default_value = .036
link(noise.outputs['Fac'],bump.inputs['Height'])
link(bump.outputs[0],bsdf.inputs['Normal'])
verts = [(x, edge(x, s)+s*.13, 0) for x in xs for s in (-1,1)]
mesh('River surface', verts, [(2*i,2*i+2,2*i+3,2*i+1) for i in range(len(xs)-1)], water)

foam = [material('Flow glint %d' % i, c, .44) for i,c in enumerate([
    (.26,.61,.57), (.38,.71,.64), (.55,.79,.70), (.13,.47,.45)])]
for i in range(148):
    x0 = rng.uniform(-24, 22)
    lane = rng.uniform(-2.31, 2.31)
    speed = 1.78 - .72*(abs(lane)/2.4)**1.6 + rng.uniform(-.14,.14)
    length = rng.uniform(.16,.88)
    width = rng.uniform(.011,.040)
    verts = []
    for j in range(9):
        t = j/8
        w = width*.5*(.018 + math.sin(math.pi*t)**.8)
        center = .035*math.sin(math.pi*t) + .044*t
        for side in (-1,1):
            verts.append((length*t, center+side*w, 0))
    ob = mesh('Current filament %03d' % i, verts,
              [(2*j,2*j+2,2*j+3,2*j+1) for j in range(8)], rng.choice(foam))
    for f in (1, 13, 25, 37, 48):
        x = x0 + speed*(f-1)/12
        ob.location = (x, channel(x)+lane, .012)
        ob.rotation_euler.z = math.atan2(channel(x+.25)-channel(x-.25),.5)
        ob.keyframe_insert(data_path='location',frame=f)
        ob.keyframe_insert(data_path='rotation_euler',frame=f)

# A few warm leaves make it easy to track the current against the fixed shore.
drift_leaf = material('Copper leaves on the water', (.59,.225,.067))
for i, (x0, lane, speed) in enumerate([(-7.1,-1.13,1.54), (-4.35,-.36,1.74),
                                        (-1.58,.90,1.59), (1.52,-1.64,1.34)]):
    ob = mesh('Drifting leaf %02d' % i,
              [(-.106,0,.003),(-.040,-.040,.004),(.030,-.032,.006),
               (.095,.008,.018),(.016,.041,.006),(-.055,.029,.003),
               (-.010,0,.020)],
              [(j,(j+1)%6,6) for j in range(6)], drift_leaf)
    for f in (1, 13, 25, 37, 48):
        x = x0 + speed*(f-1)/12
        ob.location = (x,channel(x)+lane+.045*math.sin(f*.16+i),.016)
        ob.rotation_euler.z = .38*math.sin(f*.12+i)
        ob.keyframe_insert(data_path='location',frame=f)
        ob.keyframe_insert(data_path='rotation_euler',frame=f)

# Sparse bankside clusters leave a clear silhouette around the watcher.
person_x = -2.65
person_y = edge(person_x,-1)-.87
for side in (-1,1):
    for i in range(38):
        x = rng.uniform(-16,16)
        if side < 0 and abs(x-person_x)<1.32:
            continue
        d = rng.uniform(.05,1.40)
        y = edge(x,side)+side*d
        z = .06+.31*min(1,d)
        size = rng.uniform(.075,.29)
        ob = oval('Rounded shore pebble', (x,y,z),
                  (size*1.24,size*.81,size*.52),rng.choice(stones),ico=True)
        ob.rotation_euler.z = rng.random()*math.tau

for side in (-1,1):
    for i in range(23):
        x = rng.uniform(-14,14)
        if side < 0 and abs(x-person_x)<1.65:
            continue
        d = rng.uniform(.47,2.5)
        y = edge(x,side)+side*d
        z = .22+.18*min(1,d)
        for j in range(rng.randint(5,8)):
            a = rng.random()*math.tau
            h = rng.uniform(.13,.43)
            bend = rng.uniform(.05,.20)
            dx,dy = math.cos(a),math.sin(a)
            w = rng.uniform(.017,.033)
            xx,yy = x+rng.uniform(-.08,.08),y+rng.uniform(-.08,.08)
            mesh('Sedge blade',[(xx-dy*w,yy+dx*w,z),(xx+dy*w,yy-dx*w,z),
                 (xx+dx*bend*.43+dy*w*.65,yy+dy*bend*.43-dx*w*.65,z+h*.55),
                 (xx+dx*bend,yy+dy*bend,z+h),
                 (xx+dx*bend*.43-dy*w*.65,yy+dy*bend*.43+dx*w*.65,z+h*.55)],
                 [(0,1,2,4),(4,2,3)],rng.choice(leaves))

# Build the figure facing local +Y with stable, planted feet.
def pivot(name, where, parent=None):
    ob = bpy.data.objects.new(name,None)
    scene.collection.objects.link(ob)
    ob.parent = parent
    ob.location = where
    return ob


root = pivot('Watcher on the bank',(person_x,person_y,.352))
root.rotation_euler.z = -.57
for s in (-1,1):
    y = s*.082
    x = s*.133
    oval('Flattened rubber sole',(x,y+.072,.055),(.115,.217,.051),soles,root)
    oval('Boot upper',(x,y+.054,.108),(.112,.208,.100),boots,root)
    limb('Trouser calf',(x,y-.032,.195),(x*1.04,y+.02,.50),.101,.104,pants,root)
    limb('Trouser thigh',(x*1.04,y+.02,.50),(x*.79,0,.87),.119,.122,pants,root)

body = pivot('Breathing and weight shift',(0,0,.88),root)
oval('Jacket hem',(0,0,.015),(.254,.157,.127),seam,body)
oval('Anorak body',(0,0,.205),(.301,.185,.320),jacket,body)
oval('Hood folded on back',(0,-.127,.426),(.222,.141,.139),hood,body)
oval('Collar',(0,.02,.469),(.157,.143,.076),seam,body)
for s in (-1,1):
    shoulder = (s*.252,.002,.359)
    elbow = (s*.316,.021,.167)
    cuff = (s*.241,.144,.075)
    limb('Upper sleeve',shoulder,elbow,.097,.094,jacket,body)
    limb('Bent forearm',elbow,cuff,.081,.078,jacket,body)
    oval('Cuff at pocket',cuff,(.070,.057,.062),seam,body)
    oval('Fingers at pocket',(s*.205,.160,.06),(.052,.041,.046),skin,body)

head = pivot('Head follows the current',(0,.039,.490),body)
oval('Neck',(0,.005,.045),(.094,.092,.123),skin,head)
oval('Face',(0,.032,.235),(.164,.151,.207),skin,head)
oval('Nose',(0,.175,.219),(.044,.052,.042),skin,head)
for s in (-1,1):
    oval('Ear',(s*.155,.041,.228),(.037,.042,.058),skin,head)
    eye = oval('Eye',(s*.069,.165,.267),(.025,.013,.014),eyes,head)
    eye.rotation_euler.z = -s*.31
    brow = oval('Eyebrow',(s*.070,.161,.296),(.031,.012,.008),hair,head)
    brow.rotation_euler.z = -s*.30
oval('Cropped hair',(0,-.018,.315),(.174,.153,.151),hair,head)
oval('Hair at the nape',(0,-.085,.240),(.142,.089,.127),hair,head)
fringe = oval('Side swept fringe',(-.034,.064,.368),(.148,.107,.070),hair,head)
fringe.rotation_euler.y = -.24

for f, pitch, turn, lean in [(1,-.21,.13,.025), (11,-.24,.09,.014),
                             (30,-.19,-.30,-.035), (43,-.15,-.40,-.052),
                             (48,-.15,-.37,-.049)]:
    head.rotation_euler = (pitch,0,turn)
    head.keyframe_insert(data_path='rotation_euler',frame=f)
    body.rotation_euler = (.045+lean*.2,lean,lean*.42)
    body.location.z = .88+.009*math.sin((f-1)*math.tau/47)
    body.keyframe_insert(data_path='rotation_euler',frame=f)
    body.keyframe_insert(data_path='location',frame=f)

# Keep the flow at a steady pace through the image.
for action in bpy.data.actions:
    if action == nt.animation_data.action or action.name.startswith(('Current filament','Drifting leaf')):
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation = 'LINEAR'


def aim(ob, point):
    ob.rotation_euler = (Vector(point)-ob.location).to_track_quat('-Z','Y').to_euler()


bpy.ops.object.camera_add(location=(4.0,-10.6,7.5))
cam = bpy.context.object
cam.name = 'Riverbank composition'
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 11.65
aim(cam,(.05,-.65,.18))
scene.camera = cam

world = bpy.data.worlds.new('Soft blue sky')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.52,.66,.77,1)
world.node_tree.nodes['Background'].inputs[1].default_value = .37
scene.world = world


def light(name, kind, position, target, power, color, size):
    data = bpy.data.lights.new(name,kind)
    data.energy, data.color = power,color
    if kind == 'AREA':
        data.shape, data.size = 'DISK',size
    else:
        data.angle = size
    ob = bpy.data.objects.new(name,data)
    scene.collection.objects.link(ob)
    ob.location = position
    aim(ob,target)


light('Late sun','SUN',(-5,-3,7),(0,0,0),2.05,(1,.84,.64),.19)
light('Open sky fill','AREA',(3,-1,8),(0,0,0),460,(.70,.84,1),8)
light('Far bank bounce','AREA',(-1,6,5),(-2,-3,1),340,(.63,.84,1),7)
scene.frame_set(1)
