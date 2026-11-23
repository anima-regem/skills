"""Under the Tree | Blender 5.2 | metres, seconds, 12 fps."""
from pathlib import Path
from math import cos, sin, exp, pi, radians, tanh
from random import Random

import bpy
from mathutils import Vector
from mathutils.noise import noise

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ENV = ASSETS / "environment"
rng = Random(111)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.render.engine = 'BLENDER_EEVEE'
scene.frame_start, scene.frame_end = 1, 48
scene.render.fps = 12
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'


def collection(name):
    result = bpy.data.collections.new(name)
    scene.collection.children.link(result)
    return result


set_col = collection("Oak and meadow")
wind_col = collection("Rooted plants")
leaf_col = collection("Detached oak leaves")
light_col = collection("Late afternoon")


def mesh(name, verts, faces, materials, group=set_col):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    for material in materials:
        data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    group.objects.link(obj)
    return obj


def material(name, color, roughness=.65):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    shader = result.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return result, shader


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


# Use the supplied CC BY 4.0 head as a base for the original traveler.
# Einar Rig (CC BY 4.0) Blender Foundation | studio.blender.org.
with bpy.data.libraries.load(str(ASSETS / "einar.blend"), link=False) as (_, target):
    target.collections = ["CH-einar"]
character = target.collections[0]
scene.collection.children.link(character)
character.name = "Rowan | field traveler"
rig = bpy.data.objects["RIG-einar"]
rig["Asset attribution"] = "Based on Einar Rig, Blender Foundation, CC BY 4.0 (studio.blender.org)"
root = bpy.data.objects.new("Seated body placement", None)
character.objects.link(root)
for obj in list(character.all_objects):
    if obj != root and not obj.parent and not obj.name.startswith("WGT-"):
        obj.parent = root
    if obj.name.startswith("WGT-") or obj.name in {"GEO-einar_hat", "GEO-einar_hair", "GEO-einar_hair.messy"}:
        obj.hide_render = True
root.location.z = -.57
root.rotation_euler.x = radians(-5)
bpy.context.view_layer.update()

# Keep the fabric weave, remap the canvas to faded slate blue.
for name in ("einar.jacket.canvas", "einar.jacket.rim", "einar.jacket.collar"):
    mat = bpy.data.materials.get(name)
    if mat is None or not mat.use_nodes:
        continue
    tree = mat.node_tree
    for shader in list(tree.nodes):
        if shader.type != 'BSDF_PRINCIPLED':
            continue
        color = shader.inputs['Base Color']
        if color.is_linked:
            old = color.links[0].from_socket
            tint = tree.nodes.new('ShaderNodeMixRGB')
            tint.blend_type = 'COLOR'
            tint.inputs[0].default_value = .90
            tint.inputs[2].default_value = (.033, .101, .117, 1)
            tree.links.new(old, tint.inputs[1])
            tree.links.new(tint.outputs[0], color)
        else:
            color.default_value = (.035, .08, .095, 1)

# The traveler's skin uses the supplied albedo and pore detail with a
# restrained specular response and no production bruising layer.
skin = bpy.data.materials["einar.skin"]
skin_tree = skin.node_tree
skin_nodes = skin_tree.nodes
skin_links = skin_tree.links
skin_shader = skin_nodes.new('ShaderNodeBsdfPrincipled')
skin_shader.label = "Rowan | skin in open shade"
skin_shader.inputs['Subsurface Weight'].default_value = .16
skin_shader.inputs['Subsurface Scale'].default_value = .011
skin_shader.inputs['Specular IOR Level'].default_value = .30
skin_shader.inputs['Roughness'].default_value = .54
skin_links.new(skin_nodes['Image Texture.005'].outputs['Color'], skin_shader.inputs['Base Color'])
pore = skin_nodes.new('ShaderNodeBump')
pore.inputs['Strength'].default_value = .24
pore.inputs['Distance'].default_value = .0007
skin_links.new(skin_nodes['Image Texture.002'].outputs['Color'], pore.inputs['Height'])
grain = skin_nodes.new('ShaderNodeTexNoise')
grain.inputs['Scale'].default_value = 685
grain.inputs['Detail'].default_value = 2.4
skin_space = skin_nodes.new('ShaderNodeTexCoord')
skin_links.new(skin_space.outputs['Object'], grain.inputs['Vector'])
fine_pore = skin_nodes.new('ShaderNodeBump')
fine_pore.inputs['Strength'].default_value = .15
fine_pore.inputs['Distance'].default_value = .00032
skin_links.new(pore.outputs['Normal'], fine_pore.inputs['Normal'])
skin_links.new(grain.outputs['Fac'], fine_pore.inputs['Height'])
skin_links.new(fine_pore.outputs['Normal'], skin_shader.inputs['Normal'])
skin_links.new(skin_shader.outputs['BSDF'], skin_nodes['Material Output'].inputs['Surface'])

camera_data = bpy.data.cameras.new("Portrait lens")
camera = bpy.data.objects.new("Locked three-quarter close-up", camera_data)
scene.collection.objects.link(camera)
camera.location = (.277, -.773, 1.137)
point_at(camera, (.047, .012, 1.091))
camera_data.lens = 59
camera_data.dof.use_dof = True
camera_data.dof.focus_distance = .836
camera_data.dof.aperture_fstop = 6.3
scene.camera = camera


def pose(name, prop, keys):
    bone = rig.pose.bones[name]
    for frame, value in keys:
        setattr(bone, prop, value)
        bone.keyframe_insert(data_path=prop, frame=frame, group=name)


# The target's local X points screen-left. Lead the head with a short saccade
# onto the leaf, then lower the gaze as it drops out of the foreground.
pose("MSTR-TGT-Eyes", "location", [
    (1, (-.196, 0, -.044)), (17, (-.196, 0, -.044)),
    (20, (-.515, 0, .020)), (24, (-.494, 0, -.048)),
    (28, (-.462, 0, -.135)), (32, (-.422, 0, -.224)),
    (36, (-.352, 0, -.239)), (42, (-.302, 0, -.17)), (48, (-.306, 0, -.158)),
])
pose("FK-Head", "rotation_euler", [
    (1, (radians(1), radians(-5), radians(1))),
    (21, (radians(1), radians(-5), radians(1))),
    (26, (radians(1.9), radians(.4), radians(.6))),
    (33, (radians(3.4), radians(2), radians(.35))),
    (40, (radians(3.9), radians(2.25), radians(.1))),
    (48, (radians(3.4), radians(1.9), radians(.25))),
])
pose("MSTR-Spine_Chest", "rotation_euler", [
    (1, (0, 0, 0)), (13, (.005, 0, 0)), (26, (.001, 0, 0)),
    (38, (.004, 0, 0)), (48, (-.001, 0, 0)),
])
for side, sign in (("L", 1), ("R", -1)):
    for label, amount in (("Inner", -.0037), ("Outer", -.0009)):
        pose(f"ACT-Eyebrow_{label}.{side}", "location", [
            (1, (0, amount * (1 + .15 * sign), 0)),
            (23, (0, amount, 0)), (34, (0, amount * .83, 0)),
            (42, (0, amount * .55, 0)), (48, (0, amount * .57, 0)),
        ])
    pose(f"ACT-Mouth_Corner.{side}", "location", [
        (1, (0, .0024, 0)), (32, (0, .0024, 0)),
        (38, (0, .00065, 0)), (43, (0, .00035, 0)), (48, (0, .00035, 0)),
    ])
    pose(f"Blink.{side}", "location", [
        (1, (0, -.00035, 0)), (33, (0, -.00035, 0)),
        (34.6, (0, -.0008, 0)), (36, (0, -.0062, 0)),
        (36.45, (0, -.0058, 0)), (38.35, (0, -.0002, 0)),
        (40, (0, -.00035, 0)), (48, (0, -.00035, 0)),
    ])

# The shoulder is supported by the forward-right flank of the oak.
# Corrugated radial sections and continuous UVs keep the silhouette tactile.
bark, bark_bs = material("Oak | weathered bark", (.11, .078, .045), .92)
nodes = bark.node_tree.nodes
links = bark.node_tree.links
for suffix, destination in (('diffuse', 'Base Color'), ('normal', 'Normal')):
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(ENV / f"oak_bark_{suffix}.jpg"), check_existing=True)
    if suffix == 'normal':
        tex.image.colorspace_settings.name = 'Non-Color'
        normal = nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value = 1.17
        links.new(tex.outputs['Color'], normal.inputs['Color'])
        links.new(normal.outputs['Normal'], bark_bs.inputs[destination])
    else:
        links.new(tex.outputs['Color'], bark_bs.inputs[destination])

segments, rings = 112, 77
verts, faces = [], []
for j in range(rings):
    z = -.11 + j * .048
    for i in range(segments):
        a = i * 2 * pi / segments
        rad = (.431 - .037*z + .16*exp(-max(0, z)*6)
               + .015*sin(17*a + 1.1*z) + .008*cos(29*a - 2*z)
               + .017*noise(Vector((cos(a)*3, sin(a)*3, z*2))))
        verts.append((-.373 - .035*z + rad*cos(a), .397 + .023*z + rad*sin(a), z))
for j in range(rings - 1):
    for i in range(segments):
        nxt = (i + 1) % segments
        faces.append((j*segments+i, j*segments+nxt, (j+1)*segments+nxt, (j+1)*segments+i))
trunk = mesh("Oak trunk and shoulder rest", verts, faces, [bark])
uv = trunk.data.uv_layers.new()
for poly in trunk.data.polygons:
    poly.use_smooth = True
    j, i = divmod(poly.index, segments)
    coords = ((i,j), (i+1,j), (i+1,j+1), (i,j+1))
    for loop, (u,v) in zip(poly.loop_indices, coords):
        uv.data[loop].uv = (u / segments * 2.45, v * .048 / .91)


def height(x, y):
    return .36 * tanh(max(0, y - .45) * .44) + .045*sin(y*.62 + x*.52)*tanh(max(0, y))

soil, soil_bs = material("Meadow earth | ochre and olive", (.2, .19, .064), .98)
n = soil.node_tree.nodes
l = soil.node_tree.links
coord = n.new('ShaderNodeTexCoord')
texture = n.new('ShaderNodeTexNoise')
texture.inputs['Scale'].default_value = 5.0
texture.inputs['Detail'].default_value = 3.5
l.new(coord.outputs['Object'], texture.inputs['Vector'])
ramp = n.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (.047, .055, .021, 1)
ramp.color_ramp.elements[1].color = (.33, .265, .096, 1)
l.new(texture.outputs['Fac'], ramp.inputs['Fac'])
l.new(ramp.outputs['Color'], soil_bs.inputs['Base Color'])
verts = []
faces = []
for j in range(74):
    for i in range(64):
        x, y = i*.66-30, j*.56-5
        verts.append((x,y,height(x,y)))
        if i and j:
            k = j*64+i
            faces.append((k-65,k-64,k,k-1))
ground = mesh("Rising edge of meadow", verts, faces, [soil])
for poly in ground.data.polygons:
    poly.use_smooth = True

# A translating gust flexes rooted blades, followed by damped recovery.
# Pattern reference: Dupont et al., Waving plants and turbulent eddies (2010).
# Each patch samples the gust at its centre. Lengths and wind strength are estimates.
grass_mats = []
for name, color in (
    ("Shade grass", (.084,.124,.031)), ("Olive blades", (.17,.231,.049)),
    ("Sun on grass", (.31,.33,.082)), ("Dry stems", (.44,.31,.091)),
    ("Seed heads", (.52,.404,.143)), ("Sage understory", (.086,.16,.083))
):
    m, shader = material(name, color, .81)
    shader.inputs['Subsurface Weight'].default_value = .08
    grass_mats.append(m)


def blade(verts, faces, slots, flex, x, y, z, length, w, a, lean, slot):
    start = len(verts)
    ux, uy = cos(a), sin(a)
    for i in range(5):
        t = i / 4
        cx = x + ux*lean*t*t
        cy = y + uy*lean*t*t
        zz = z + length*t - lean*.20*t*t*t
        width = w*(.55+.58*sin(pi*t))*(1.0-.97*t**5)
        verts.extend(((cx-uy*width,cy+ux*width,zz),
                      (cx,cy,zz+width*.22),
                      (cx+uy*width,cy-ux*width,zz)))
        flex.extend((t*t*length,)*3)
        if i:
            k = start+i*3
            faces.extend(((k-3,k-2,k+1,k), (k-2,k-1,k+2,k+1)))
            slots.extend((slot,slot))


def smoothstep(x):
    x = min(1, max(0, x))
    return x*x*(3-2*x)


def linear(action):
    for layer in action.layers:
        for strip in layer.strips:
            for channel in strip.channelbags:
                for curve in channel.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'


for row in range(18):
    for col in range(12):
        # The shot looks diagonally left into the field.
        px = 1.59 - col*.52 - row*.16
        py = .83 + row*.55
        verts, faces, slots, flex = [], [], [], []
        for _ in range(24 if row < 12 else 13):
            x, y = px+rng.uniform(-.28,.28), py+rng.uniform(-.3,.3)
            z = height(x,y)-.01
            clump = rng.uniform(.34,.81)
            for k in range(rng.randint(3,6)):
                blade(verts, faces, slots, flex, x+rng.uniform(-.037,.037), y+rng.uniform(-.037,.037), z,
                      clump*rng.uniform(.57,1.14), rng.uniform(.008,.023), rng.uniform(0,2*pi),
                      rng.uniform(.08,.29), rng.choices(range(6), [2,5,5,2,0,2])[0])
            if rng.random() < .34:
                a = rng.uniform(0,2*pi)
                length = clump*1.18
                blade(verts, faces, slots, flex, x,y,z,length,.005,a,.093,3)
                for seed in range(4):
                    t = .81 + .044*seed
                    blade(verts,faces,slots,flex,x+.093*t*t*cos(a),y+.093*t*t*sin(a),
                          z+length*t-.0186*t**3,.074,.011,a+(-1)**seed*.84,.023,4)
                    flex[-15:] = [length*t*t + (.074*(i//3/4)**2) for i in range(15)]
        patch = mesh(f"Meadow patch {row:02d}.{col:02d}", verts,faces,grass_mats,wind_col)
        for poly, idx in zip(patch.data.polygons, slots):
            poly.material_index = idx
        patch.shape_key_add(name="Rooted rest")
        bend = patch.shape_key_add(name="Downwind flex")
        bend.slider_min = -.35
        for i, weight in enumerate(flex):
            bend.data[i].co.x -= .54*weight
            bend.data[i].co.y += .22*weight
            bend.data[i].co.z -= .13*weight
        delay = 1.07 + .125*(1.59-px) + .027*row
        phase = rng.uniform(0,2*pi)
        for f in (*range(1,49,2), 48):
            u = (f-1)/12 - delay
            pulse = smoothstep(u/.28) * (1-smoothstep((u-.29)/.73))
            tail = max(0,u-.64)
            ring = .21*sin(2*pi*1.85*tail)*exp(-4*tail) if tail else 0
            bend.value = .035*sin(.07*f+phase) + pulse*(.80+.12*sin(11*u+phase)) + ring
            bend.keyframe_insert(data_path="value", frame=f)
        linear(patch.data.shape_keys.animation_data.action)


# Leaves enter from the canopy above frame with velocities already acquired
# during the unseen drop. An air-drag approximation gives drifting flutter
# and occasional tumble (Belmonte, Eisenberg & Moses, PRL 81, 345).
# The hero leaf settles at a deliberately slow estimated 0.21 m/s for readability.
leaf_materials = []
for name, color in (("Ochre", (.48,.19,.035)), ("Copper", (.31,.082,.021)),
                    ("Olive gold", (.30,.229,.041)), ("Raised veins", (.33,.14,.041))):
    mat, bs = material(name, color, .57)
    bs.inputs['Subsurface Weight'].default_value = .17
    leaf_materials.append(mat)

def make_leaf(label, size, color):
    verts, faces = [], []
    outline = [0,.12,.44,.34,.78,.47,1,.63,.89,.46,.63,.33,0]
    for i, width in enumerate(outline):
        t = i/(len(outline)-1)
        for side in (-1,0,1):
            verts.append((side*.34*width*size, (t-.46)*size,
                          (.16*(t-.44)**2 + .13*width*abs(side) - .028*t*side)*size))
        if i:
            k = i*3
            faces += [(k-3,k-2,k+1,k), (k-2,k-1,k+2,k+1)]
    leaf = mesh(label,verts,faces,[leaf_materials[color]],leaf_col)
    for poly in leaf.data.polygons:
        poly.use_smooth = True
    vein = bpy.data.curves.new(label+" veins", 'CURVE')
    vein.dimensions = '3D'
    vein.bevel_depth = size*.009
    vein.bevel_resolution = 1
    vein.materials.append(leaf_materials[3])
    def line(points):
        spline = vein.splines.new('POLY')
        spline.points.add(len(points)-1)
        for p, co in zip(spline.points, points):
            p.co = (*co, 1)
    line([(0,(i/12-.46)*size,(.16*(i/12-.44)**2+.012)*size) for i in range(-2,13)])
    for j in (3,5,7,9):
        for side in (-1,1):
            line([(0,(j/12-.49)*size,.013*size),
                  (side*.25*outline[j+1]*size,((j+1)/12-.46)*size,.106*outline[j+1]*size)])
    ribs = bpy.data.objects.new(label+" | veins and petiole", vein)
    leaf_col.objects.link(ribs)
    ribs.parent = leaf
    return leaf


paths = [
    ("Tracked oak leaf", .047, 0, .227, -.260, 1.250, 1.15, .207, -.018, .49),
    ("First leaf behind him", .058, 1, .31, .28, 1.45, .84, .37, -.073, 2.7),
    ("Higher gold leaf", .064, 0, .322, .42, 1.55, 1.47, .31, -.049, 4.15),
    ("Leaf over sunlit field", .085, 2, .24, .93, 1.52, 1.9, .295, -.09, 3.48),
    ("Late copper leaf", .056, 1, .224, .16, 1.47, 2.50, .222, -.042, 1.31),
    ("Far gold leaf", .105, 0, -.22, 1.55, 1.60, 2.61, .36, -.061, 2.51),
    ("Near falling leaf", .040, 2, .246, -.435, 1.32, 2.86, .35, .042, 5.0),
]
for label, size, color, x,y,z, release, speed, drift, phase in paths:
    leaf = make_leaf(label, size, color)
    for f in range(1,49):
        shot_time = (f-1)/12
        t = shot_time - release
        gust = .018 * smoothstep((shot_time-1.12)/1.30)
        flutter = sin(9.1*t+phase)
        leaf.location = (x+drift*t-gust+.022*flutter,
                         y+.028*sin(6.9*t+phase),
                         z-speed*t+.011*cos(10*t+phase))
        leaf.rotation_euler = (1.02+.58*sin(10*t+phase),
                               .72*sin(7.7*t+phase) + (.45 if color==0 else 1.75)*t,
                               phase+1.5*t+.64*flutter)
        leaf.keyframe_insert(data_path="location", frame=f)
        leaf.keyframe_insert(data_path="rotation_euler", frame=f)
    linear(leaf.animation_data.action)

world = bpy.data.worlds.new("Autumn daylight")
scene.world = world
world.use_nodes = True
tree = world.node_tree
hdr = tree.nodes.new('ShaderNodeTexEnvironment')
hdr.image = bpy.data.images.load(str(ENV / "autumn_meadow_1k.hdr"), check_existing=True)
tree.links.new(hdr.outputs['Color'], tree.nodes.get('Background').inputs['Color'])
tree.nodes.get('Background').inputs['Strength'].default_value = .43


def light(name, kind, position, target, energy, color, size):
    data = bpy.data.lights.new(name, kind)
    data.energy, data.color = energy, color
    if kind == 'AREA':
        data.shape, data.size = 'DISK', size
    else:
        data.angle = size
    obj = bpy.data.objects.new(name,data)
    light_col.objects.link(obj)
    obj.location = position
    point_at(obj,target)
    return obj


light("Low sun across open field", 'SUN', (3,4,2.2), (0,0,.2), 2.35, (1,.79,.51), .15)
light("Open sky along edge of canopy", 'AREA', (1.15,-.47,2.05), (0,0,1.04), 27, (.70,.82,1), 1.3)
light("Warm grass bounce", 'AREA', (.33,-1.14,.65), (0,0,1.06), 12, (1,.80,.61), 1.10)
light("Light grazing the shoulder", 'AREA', (.55,.68,1.9), (0,.09,1.1), 33, (1,.75,.44), .63)

for frame, name in ((1,"Watch"), (13,"Gust reaches meadow"), (18,"Eyes pick up leaf"),
                    (21,"Head follows"), (32,"Gust tapers"), (36,"Blink"), (43,"Hold")):
    scene.timeline_markers.new(name, frame=frame)
scene.frame_set(1)
