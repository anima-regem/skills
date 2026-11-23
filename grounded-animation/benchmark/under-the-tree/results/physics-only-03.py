"""Under the Tree. Build with Blender in background mode using --python scene.py.

Character base: Einar Rig, Blender Foundation (CC BY 4.0, studio.blender.org).
Oak bark textures: Charlotte Baglioni / Poly Haven (CC0).
"""
import math
import random
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Vector

ASSETS = Path(__file__).resolve().parent / "assets"
ENV = ASSETS / "environment"
FPS = 12
END = 48
TAU = math.tau
rng = random.Random(16209)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, END
scene.unit_settings.system = 'METRIC'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'


def mesh(name, vertices, faces, materials=()):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    for mat in materials:
        data.materials.append(mat)
    return obj


def surface(name, color, roughness=.7):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat, bsdf


def ramp(tree, source, stops):
    node = tree.nodes.new('ShaderNodeValToRGB')
    elements = node.color_ramp.elements
    for i, (pos, color) in enumerate(stops):
        elem = elements[i] if i < 2 else elements.new(pos)
        elem.position, elem.color = pos, (*color, 1)
    tree.links.new(source, node.inputs[0])
    return node.outputs[0]


def texture_color(mat, bsdf, scale, stops):
    tree = mat.node_tree
    noise = tree.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = 3.0
    coords = tree.nodes.new('ShaderNodeTexCoord')
    tree.links.new(coords.outputs['Object'], noise.inputs['Vector'])
    tree.links.new(ramp(tree, noise.outputs['Fac'], stops), bsdf.inputs['Base Color'])
    return noise


def recolor(material, multiplier):
    tree = material.node_tree
    for node in list(tree.nodes):
        if node.type not in {'BSDF_PRINCIPLED', 'BSDF_DIFFUSE'}:
            continue
        socket = node.inputs.get('Base Color') or node.inputs.get('Color')
        if socket and socket.is_linked:
            original = socket.links[0].from_socket
            mix = tree.nodes.new('ShaderNodeMixRGB')
            mix.blend_type = 'MULTIPLY'
            mix.inputs[0].default_value = 1
            mix.inputs[2].default_value = (*multiplier, 1)
            tree.links.new(original, mix.inputs[1])
            tree.links.new(mix.outputs[0], socket)


# The original shot character, Calder, uses the supplied production rig as a base.
with bpy.data.libraries.load(str(ASSETS / "einar.blend"), link=False) as (_, target):
    target.collections = ["CH-einar"]
character = target.collections[0]
character.name = "Calder"
scene.collection.children.link(character)
rig = bpy.data.objects["RIG-einar"]
rig.location.z -= .63
rig["Character"] = "Calder"
rig["Base asset credit"] = "Einar Rig (CC BY 4.0) Blender Foundation | studio.blender.org"
bpy.data.objects["GEO-einar_hat"].hide_render = True
recolor(bpy.data.materials["einar.hair"], (.50, .41, .32))
recolor(bpy.data.materials["eyes.iris"], (.73, .93, .72))

# A weathered teal work jacket with woven fibers and muted contrasting trim.
canvas, fabric = surface("Calder • faded spruce canvas", (.046, .115, .106), .82)
fabric.inputs['Sheen Weight'].default_value = .24
texture_color(canvas, fabric, 5.5, [
    (.18, (.022, .047, .044)), (.82, (.085, .164, .149))])
tree = canvas.node_tree
grain = tree.nodes.new('ShaderNodeTexNoise')
grain.inputs['Scale'].default_value = 590
tree.links.new(next(n for n in tree.nodes if n.type == 'TEX_COORD').outputs['Object'], grain.inputs[0])
bump = tree.nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .27
bump.inputs['Distance'].default_value = .00065
tree.links.new(grain.outputs['Fac'], bump.inputs['Height'])
tree.links.new(bump.outputs[0], fabric.inputs['Normal'])
trim, _ = surface("Calder • bound edges", (.024, .065, .059), .92)
for name in ("jacket_main", "jacket_collar1", "jacket_collar2"):
    slots = bpy.data.objects["GEO-einar_" + name].data.materials
    slots[0] = canvas
    for i in range(1, len(slots)):
        slots[i] = trim


def pose_track(name, prop, samples):
    bone = rig.pose.bones[name]
    for frame, value in samples:
        setattr(bone, prop, value)
        bone.keyframe_insert(data_path=prop, frame=frame, group=name)


def head_keys(samples):
    return [(f, tuple(math.radians(a) for a in angles)) for f, angles in samples]


# The shoulder stays against the trunk. Breathing is a small upper-chest motion.
pose_track('MSTR-Spine_Chest', 'rotation_euler', head_keys([
    (1, (0,0,0)), (12, (.29,0,0)), (24, (-.15,0,0)),
    (35, (.26,0,0)), (48, (-.11,0,0))]))
pose_track('FK-Head', 'rotation_euler', head_keys([
    (1, (-2.0,.0,-2.2)), (18, (-2.0,.1,-2.2)), (23, (-1.0,1.7,-2.8)),
    (30, (1.7,4.0,-3.4)), (35, (2.6,4.4,-3.5)), (48, (2.4,4.2,-3.3))]))
pose_track('MSTR-TGT-Eyes','location', [
    (1, (.052,0,.027)), (14, (.052,0,.027)), (16, (.132,0,.215)),
    (19, (.236,0,.074)), (23, (.42,0,-.17)), (29, (.44,0,-.225)),
    (33, (.38,0,-.17)), (36, (.32,0,-.13)),
    (41, (.28,0,-.092)), (48, (.28,0,-.090))])
for side, tension in [('L', 1), ('R', .81)]:
    pose_track('ACT-Eyebrow_Inner.'+side, 'location', [
        (f, (0,y*tension,0)) for f,y in
        [(1,-.0027), (13,-.0027), (18,-.0036), (29,-.0020), (42,-.0012), (48,-.0012)]])
    pose_track('Blink.'+side, 'location', [
        (f,(0,y,0)) for f,y in [(1,0), (34,0), (35,-.0026), (36,-.006),
                                (37,-.0024), (39,0), (48,0)]])
    pose_track('ACT-Mouth_Corner.'+side, 'location', [
        (f,(x*tension,y,0)) for f,x,y in
        [(1,-.0014,.0017), (31,-.0014,.0017), (37,-.00075,.0009),
         (43,-.00018,.00015), (48,-.00018,.00015)]])
pose_track('MSTR-Jaw', 'rotation_euler', head_keys([
    (1,(-1.45,0,0)), (33,(-1.45,0,0)), (41,(-.28,0,0)), (48,(-.28,0,0))]))

# The camera sits at seated eye height. Screen left is reserved for the field
# and the near leaf. Focus covers both eyes and the mouth.
def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z','Y').to_euler()


camera = bpy.data.objects.new("Close-up", bpy.data.cameras.new("Close-up"))
scene.collection.objects.link(camera)
camera.location = (.307,-.811,1.114)
aim(camera, (.022,-.064,1.016))
camera.data.lens = 54
camera.data.clip_start = .035
camera.data.dof.use_dof = True
camera.data.dof.focus_distance = .771
camera.data.dof.aperture_fstop = 7.1
camera.data.dof.aperture_blades = 8
scene.camera = camera
bpy.context.view_layer.update()


def light(name, kind, location, target, power, color, size):
    data = bpy.data.lights.new(name, kind)
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)
    data.energy, data.color = power, color
    if kind == 'AREA':
        data.shape, data.size = 'DISK', size
    else:
        data.angle = size
    return obj


world = bpy.data.worlds.new("Late afternoon sky")
scene.world = world
world.use_nodes = True
tree = world.node_tree
coords = tree.nodes.new('ShaderNodeTexCoord')
axis = tree.nodes.new('ShaderNodeSeparateXYZ')
tree.links.new(coords.outputs['Normal'], axis.inputs[0])
sky = tree.nodes.new('ShaderNodeMapRange')
sky.inputs['From Min'].default_value = -.29
sky.inputs['From Max'].default_value = .035
tree.links.new(axis.outputs['Z'], sky.inputs[0])
bg = tree.nodes.get('Background')
tree.links.new(ramp(tree, sky.outputs[0], [
    (0,(.24,.43,.66)), (1,(.85,.73,.48))]), bg.inputs[0])
bg.inputs['Strength'].default_value = .66
light("Late afternoon sun", 'SUN', (-5,4,4.5), (0,0,.6), 2.3, (1,.74,.44), .12)
light("Cool opening in the canopy", 'AREA', (-.48,-.64,1.87), (0,0,1.05),
      30, (.79,.88,1), 1.12)
light("Meadow bounce", 'AREA', (.52,-.35,.71), (0,0,1.05), 6.5,(1,.82,.62), .83)
light("Low sun through oak", 'AREA', (-.54,.38,1.50),(0,0,1.04), 17,(1,.72,.38), .47)

# The trunk supports his shoulder at the front of the lower flare.
bark, bsdf = surface("Oak • fissured bark", (.12,.08,.05), .86)
tree = bark.node_tree
uv = tree.nodes.new('ShaderNodeTexCoord')
for filename, is_normal in [('oak_bark_diffuse.jpg',False), ('oak_bark_normal.jpg',True)]:
    image = tree.nodes.new('ShaderNodeTexImage')
    image.image = bpy.data.images.load(str(ENV / filename))
    image.image.pack()
    tree.links.new(uv.outputs['UV'], image.inputs['Vector'])
    if is_normal:
        image.image.colorspace_settings.name = 'Non-Color'
        normal = tree.nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value = 1.17
        tree.links.new(image.outputs[0],normal.inputs['Color'])
        tree.links.new(normal.outputs[0],bsdf.inputs['Normal'])
    else:
        tree.links.new(image.outputs[0],bsdf.inputs['Base Color'])
verts, faces = [], []
rings, sides = 48, 112
for j in range(rings+1):
    z = -.16 + 3.8*j/rings
    for i in range(sides):
        a = TAU*i/sides
        radius = (.321 + .093*math.exp(-max(z,0)*2.4) - .024*z
                  + .014*math.sin(6*a+.9*z) + .009*math.sin(17*a-1.3*z)
                  + .005*math.sin(39*a+2.1*z))
        verts.append((.183+.022*z+radius*math.cos(a), .466+.01*z+radius*math.sin(a), z))
for j in range(rings):
    for i in range(sides):
        k = (i+1)%sides
        faces.append((j*sides+i,j*sides+k,(j+1)*sides+k,(j+1)*sides+i))
oak = mesh("Field oak", verts, faces, [bark])
layer = oak.data.uv_layers.new()
for poly in oak.data.polygons:
    poly.use_smooth = True
    j,i = divmod(poly.index,sides)
    for loop,(u,v) in zip(poly.loop_indices,[(i,j),(i+1,j),(i+1,j+1),(i,j+1)]):
        layer.data[loop].uv = (u/sides*4.7, v/rings*7.5)


def ground_height(x, y):
    dist = max(y-1,0)
    return (.045*math.sin(x*1.7+y*.4)*min(1,dist)
            + .13*math.sin(y*1.16)*min(1,dist)
            + .58*math.sin(x*.29+y*.21)*min(1,dist/9))


ground, bsdf = surface("Meadow floor", (.16,.18,.06))
texture_color(ground, bsdf, 1.35, [
    (.15,(.057,.075,.023)), (.78,(.35,.31,.105)), (.94,(.41,.40,.16))])
verts, faces = [], []
for j in range(61):
    y = -3+j*.66
    for i in range(91):
        x = -39+i*.86
        verts.append((x,y,ground_height(x,y)))
for j in range(60):
    for i in range(90):
        n=j*91+i
        faces.append((n,n+1,n+92,n+91))
field = mesh("Rolling meadow", verts, faces, [ground])
for p in field.data.polygons:
    p.use_smooth = True

# Sparse distant hedgerow with one broken edge; real silhouettes soften in DOF.
hedge_materials = [surface("Hedge %d"%i, color)[0] for i,color in enumerate([
    (.073,.106,.054),(.105,.139,.069),(.138,.151,.068),(.082,.126,.09)])]
hedge_data = bpy.data.meshes.new("Hedgerow crown")
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1)
bm.to_mesh(hedge_data)
bm.free()
hedge_data.materials.append(hedge_materials[0])
for poly in hedge_data.polygons:
    poly.use_smooth = True
for i in range(65):
    x = -30 + i*.62
    y = 24 + rng.uniform(-2.7,2.7)
    if rng.random() < .14:
        continue
    radius = rng.uniform(.45,1.22)
    shrub = bpy.data.objects.new("Far hedgerow", hedge_data)
    scene.collection.objects.link(shrub)
    shrub.location = (x,y,ground_height(x,y)+radius*.58)
    shrub.scale = (radius*rng.uniform(.8,1.5),radius,radius*rng.uniform(.75,1.4))
    shrub.material_slots[0].link = 'OBJECT'
    shrub.material_slots[0].material = rng.choice(hedge_materials)


def smoothstep(a, b, t):
    p = min(1,max(0,(t-a)/(b-a)))
    return p*p*(3-2*p)


def gust(t):
    return smoothstep(.91,1.45,t) * (1-smoothstep(2.24,3.13,t))


# Fixed-step, damped cantilever approximation. Roots stay in the soil. Each
# patch receives the gust later than the previous one, across the open ground.
# Frequencies, drag and shelter factors are shot estimates in meters/seconds.
palette = [surface("Meadow blades %d"%i,c)[0] for i,c in enumerate([
    (.103,.165,.025),(.19,.241,.035),(.26,.294,.067),(.36,.32,.082),
    (.44,.358,.127),(.34,.40,.103),(.098,.136,.046),(.54,.405,.158)])]

for band in range(16):
    verts, faces, colors = [], [], []
    for i in range(91):
        y = rng.uniform(.96, 15)
        x = -y*.77+band*(.125+y*.032)+rng.uniform(-.1,.13)
        z = ground_height(x,y)
        h = rng.uniform(.20,.64) * (1 if y>2 else 1.22)
        stems = rng.randrange(4,10)
        for k in range(stems):
            a = rng.uniform(0,TAU)
            height = h*rng.uniform(.30,1.25)
            width = rng.uniform(.007,.024)
            offset = rng.uniform(.014,.11)
            base = Vector((x+offset*math.cos(a),y+offset*math.sin(a),z-.036))
            along = Vector((math.cos(a),math.sin(a),0))
            across = Vector((-math.sin(a),math.cos(a),0))*width
            start = len(verts)
            for j in range(5):
                s = j/4
                center = base + along*(height*rng.uniform(.43,.50)*s*s)
                center.z += height*(s-.18*s**3)
                edge = across*(max(.017,(1-s)**.62) * (.30+.83*math.sin(math.pi*s*.85)))
                verts.extend((tuple(center-edge),tuple(center+edge)))
            for j in range(4):
                faces.append(tuple(start+2*j+i for i in (0,1,3,2)))
                colors.append((k+i)%7)
            if k==0 and i%3==0:
                # Small straw seed head, tapering toward the awns.
                p = Vector(verts[-1])
                for j in range(6):
                    shift = (-1)**j
                    h0 = p + Vector((.017*j/6,0,.013*j))
                    q = h0 + across*shift*1.75 + Vector((0,0,.025))
                    start = len(verts)
                    verts.extend((h0, h0-along*.006+Vector((0,0,.013)), q,
                                  h0+along*.006+Vector((0,0,.009))))
                    faces.append((start,start+1,start+2,start+3))
                    colors.append(7)
    obj = mesh("Wind patch %02d"%band, verts, faces, palette)
    for poly, index in zip(obj.data.polygons, colors):
        poly.material_index = index
    obj.shape_key_add(name="Rest")
    bend = obj.shape_key_add(name="Downwind")
    for v, key in zip(verts,bend.data):
        x,y,z=v
        span = max(0,z-ground_height(x,y)+.028)
        key.co.x -= 1.06*span**1.7
        key.co.y += .38*span**1.7
        key.co.z -= .31*span**1.55
    angle = speed = 0
    spring = 40 + (band%4)*4
    damping = 6.8
    delay = .035*(15-band)
    bend.slider_min = -.20
    bend.slider_max = 1.3
    for f in range(1,END+1):
        bend.value = angle
        bend.keyframe_insert(data_path='value',frame=f)
        for sub in range(10):
            t = (f-1+sub/10)/FPS - delay
            load = gust(t)*(.67+.19*math.sin(12*t+.20*band)+.09*math.sin(23*t))
            speed += (spring*(load-angle)-damping*speed)/(FPS*10)
            angle += speed/(FPS*10)


leaf_colors = [(.52,.155,.022),(.72,.32,.045),(.40,.077,.014),(.59,.236,.030)]
leaf_materials = []
for idx, color in enumerate(leaf_colors):
    mat, bsdf = surface("Oak leaf %d"%idx,color,.64)
    texture_color(mat, bsdf, 170, [(0,tuple(c*.32 for c in color)),(1,color)])
    bsdf.inputs['Subsurface Weight'].default_value = .11
    bsdf.inputs['Subsurface Scale'].default_value = .003
    leaf_materials.append(mat)
vein, _ = surface("Leaf midrib and stem", (.24,.11,.029))


def leaf_mesh(name, length, color):
    verts, faces = [], []
    steps = 28
    for i in range(steps+1):
        s = i/steps
        mid = .085*math.sin(s*math.pi)-.04*s
        w = .30*math.sin(math.pi*s)**.67 * (.70+.25*math.cos(TAU*(s*4.2-.14)))
        for side in (-1,0,1):
            verts.append((length*w*side, length*(s-.49),
                          length*(mid+abs(side)*w*(.22-.51*s))))
    for i in range(steps):
        for j in range(2):
            k = i*3+j
            faces.append((k,k+1,k+4,k+3))
    n = len(verts)
    for i in range(steps+1):
        s = i/steps
        z = length*(.085*math.sin(s*math.pi)-.04*s)+.00020
        verts.extend(((-length*.012,length*(s-.66),z),
                      ( length*.012,length*(s-.66),z)))
    for i in range(steps):
        k = n+i*2
        faces.append((k,k+1,k+3,k+2))
    obj = mesh(name, verts, faces, [leaf_materials[color],vein])
    for poly in obj.data.polygons:
        poly.use_smooth = True
        poly.material_index = int(poly.index >= steps*2)
    return obj


def screen_point(u,v,depth):
    # Coordinates at a plane perpendicular to the camera's optical axis.
    horizontal = camera.data.sensor_width/camera.data.lens
    offset = Vector(((u-.5)*depth*horizontal,
                     (v-.5)*depth*horizontal*360/640, -depth))
    return camera.matrix_world @ offset


# Reduced drag/lift model, informed by falling-sheet flutter observations
# (Belmonte et al., Phys. Rev. Lett. 81, 345; doi:10.1103/PhysRevLett.81.345).
# Tuned effective drag and flutter torque for small dry oak leaves. The canopy
# above the crop supplies each leaf. Release inherits branch sway velocity.
# The featured leaf crosses the gap to the left of the face.
for i,(u,v,depth,release,length,terminal) in enumerate([
    (.301,1.09,.63,1.06,.042,.268),
    (.12,1.13,1.15,1.23,.058,.48),
    (.44,1.22,1.64,1.30,.074,.60),
    (.06,1.17,2.02,1.62,.070,.42),
    (.41,1.10,1.33,2.22,.053,.37),
    (.23,1.14,1.62,2.52,.077,.422),
    (.13,1.13,1.23,2.72,.049,.46),
    (.32,1.16,2.21,2.80,.076,.50),
]):
    obj = leaf_mesh("Featured oak leaf" if i==0 else "Falling oak leaf %02d"%i,length,i%4)
    origin = screen_point(u,v,depth)
    pos = origin.copy()
    velocity = Vector((-.04,.02,0))
    phase = i*1.86+.54
    release_angle = Vector((.55+.08*i,.23,.2+phase))
    angle = release_angle.copy()
    spin = Vector((.72,1.30,.61))
    dt = 1/(FPS*20)
    for f in range(1,END+1):
        obj.location = pos
        obj.rotation_euler = Euler(angle)
        obj.keyframe_insert(data_path='location',frame=f)
        obj.keyframe_insert(data_path='rotation_euler',frame=f)
        for s in range(20):
            t = (f-1+s/20)/FPS
            if t < release:
                local = (t-release)*6
                pos.x = origin.x - .0067*math.sin(local)
                velocity.x = -.0402*math.cos(local)
                angle = release_angle + spin*(math.sin(local)/6)
                continue
            breeze = gust(t)*(.115 if i==0 else .26)
            wind = Vector((-.038-breeze,.053+breeze*.18,0))
            rel = wind - velocity
            incidence = .79+.21*abs(math.cos(angle.x)*math.cos(angle.y))
            drag_z = 9.81/terminal**2 * incidence*rel.z*abs(rel.z)
            angular_time = 12.7*(t-release)+phase
            flutter = math.sin(angular_time)
            acceleration = Vector((6.4*rel.x+1.45*flutter,
                                   4.8*rel.y+.57*math.cos(angular_time),
                                   -9.81+drag_z))
            floor = ground_height(pos.x,pos.y) + length*.22
            if pos.z > floor or velocity.z > 0:
                velocity += acceleration*dt
                pos += velocity*dt
                if pos.z <= floor:
                    pos.z = floor
                    velocity *= 0
                    spin *= 0
                spin += (Vector((18*flutter,10*math.cos(angular_time),3.5))-spin*1.85)*dt
                angle += spin*dt

for frame, label in [(1,"Watch"),(13,"Breeze"),(16,"Eyes find the leaf"),
                     (21,"Head follows"),(32,"Gust fades"),(36,"Blink"),(43,"Hold")]:
    scene.timeline_markers.new(label,frame=frame)
scene.frame_set(1)
