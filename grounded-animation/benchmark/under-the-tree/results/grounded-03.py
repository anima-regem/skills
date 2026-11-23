"""Under the Tree. Run from Blender 5.2 factory startup in background mode.

Character adapted from Einar Rig, Blender Foundation, CC BY 4.0.
https://studio.blender.org/characters/einar/v1/
Jolcham Oak Bark, Charlotte Baglioni / Poly Haven, CC0.
"""
from math import cos, sin, pi, exp
from pathlib import Path
import random

import bpy
import numpy as np
from mathutils import Vector

ASSETS = Path(__file__).resolve().parent / "assets"
ENV = ASSETS / "environment"
rng = random.Random(614)
scene = bpy.context.scene
for obj in list(scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.frame_start, scene.frame_end = 1, 48
scene.render.fps = 12
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 16
scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'


def material(name, color, roughness=.75):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return mat


def mesh(name, vertices, faces, materials, indices=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    for mat in materials:
        data.materials.append(mat)
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    if indices is not None:
        for poly, index in zip(data.polygons, indices):
            poly.material_index = index
    return obj


def point_at(obj, xyz):
    obj.rotation_euler = (Vector(xyz) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def position_keys(bone, keys, channel='location'):
    control = rig.pose.bones[bone]
    for frame, value in keys:
        setattr(control, channel, value)
        control.keyframe_insert(data_path=channel, frame=frame, group=bone)


with bpy.data.libraries.load(str(ASSETS / "einar.blend"), link=False) as (_, target):
    target.collections = ["CH-einar"]
character = target.collections[0]
scene.collection.children.link(character)
character.name = "Rowan | seated field naturalist"
rig = bpy.data.objects["RIG-einar"]
rig.animation_data_clear()
rig.location.z -= .64
rig["Asset credit"] = "Adapted from Einar Rig, Blender Foundation, CC BY 4.0"
for obj in character.all_objects:
    if obj.name.startswith("WGT-") or obj.name.endswith(".messy"):
        obj.hide_render = True
for name in ("cornea", "meniscus"):
    for side in ('L', 'R'):
        bpy.data.objects[f"GEO-eye.{name}.{side}"].hide_render = True

# Rowan's facial proportions are layered over the source expression shapes.
head = bpy.data.objects["GEO-einar_head"]
identity = head.shape_key_add(name="Rowan | nasal bridge and cheek planes", from_mix=False)
for point in identity.data:
    x, y, z = point.co
    bridge = exp(-((z-1.596)/.024)**2 - (x/.027)**2 - ((y+.145)/.045)**2)
    cheek = exp(-((z-1.573)/.032)**2 - ((abs(x)-.058)/.031)**2 - ((y+.093)/.053)**2)
    point.co.x += x*(.16*bridge - .065*cheek)
    point.co.y += .008*bridge - .004*cheek
identity.value = 1

# Regrade the source costume and grooming while keeping its material detail.
def tint_shader(tree, color, strength):
    for node in list(tree.nodes):
        if node.type == 'BSDF_PRINCIPLED':
            socket = node.inputs['Base Color']
        elif node.type == 'BSDF_DIFFUSE':
            socket = node.inputs['Color']
        else:
            continue
        mix = tree.nodes.new('ShaderNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = strength
        mix.inputs[2].default_value = (*color, 1)
        if socket.is_linked:
            tree.links.new(socket.links[0].from_socket, mix.inputs[1])
        else:
            mix.inputs[1].default_value = socket.default_value
        tree.links.new(mix.outputs[0], socket)

canvas = bpy.data.materials["einar.jacket.canvas"]
canvas_group = next(n for n in canvas.node_tree.nodes if n.type == 'GROUP')
tint_shader(canvas_group.node_tree, (.29, .61, .73), .93)
for name, color in (
    ('einar.jacket.rim', (.37, .62, .66)),
    ('einar.sweater', (.72, .46, .31)),
):
    tint_shader(bpy.data.materials[name].node_tree, color, .95)

# Use the packed production maps with soft skin and dry, dark grooming in Eevee.
def image_texture(tree, name, uv_layer=None):
    texture = tree.nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images[name]
    if uv_layer:
        uv = tree.nodes.new('ShaderNodeUVMap')
        uv.uv_map = uv_layer
        tree.links.new(uv.outputs['UV'], texture.inputs['Vector'])
    return texture


skin = material("Rowan | skin", (.40,.22,.15), .48)
nodes = skin.node_tree
shader = nodes.nodes.get('Principled BSDF')
shader.inputs['Subsurface Weight'].default_value = .075
shader.inputs['Subsurface Scale'].default_value = .013
albedo = image_texture(nodes, 'einar_skin.albedo', 'UVMap')
tone = nodes.nodes.new('ShaderNodeHueSaturation')
tone.inputs['Saturation'].default_value = .78
nodes.links.new(albedo.outputs['Color'], tone.inputs['Color'])
nodes.links.new(tone.outputs['Color'], shader.inputs['Base Color'])
detail = image_texture(nodes, 'disp_default', 'UVMap')
bump = nodes.nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .29
bump.inputs['Distance'].default_value = .0014
nodes.links.new(detail.outputs['Color'], bump.inputs['Height'])
nodes.links.new(bump.outputs['Normal'], shader.inputs['Normal'])
head.data.materials[0] = skin

hair = material("Rowan | warm dark hair", (.044,.024,.015), .68)
nodes = hair.node_tree
shader = nodes.nodes.get('Principled BSDF')
shader.inputs['Specular IOR Level'].default_value = .23
info = nodes.nodes.new('ShaderNodeHairInfo')
shade = nodes.nodes.new('ShaderNodeValToRGB')
shade.color_ramp.elements[0].color = (.013,.006,.0035,1)
shade.color_ramp.elements[1].color = (.107,.071,.044,1)
nodes.links.new(info.outputs['Random'], shade.inputs[0])
nodes.links.new(shade.outputs[0], shader.inputs['Base Color'])
for obj in character.all_objects:
    if obj.type == 'CURVES':
        for slot in obj.material_slots:
            if slot.material and slot.material.name in {'einar.hair', 'eyelashes'}:
                slot.material = hair

# Shorten the groom from each attached root to expose the eyelids and lip line.
for part, length_scale, radius_scale in [
    ('eyebrows', .49, .68), ('beard', .67, .84),
    ('mustache', .49, .73), ('hair', .81, .83),
]:
    data = bpy.data.objects['GEO-einar_' + part].data
    starts = np.empty(len(data.curves), dtype=np.int32)
    counts = np.empty_like(starts)
    data.curves.foreach_get('first_point_index', starts)
    data.curves.foreach_get('points_length', counts)
    positions = np.empty((len(data.points), 3), dtype=np.float32)
    data.position_data.foreach_get('vector', positions.ravel())
    roots = np.repeat(positions[starts], counts, axis=0)
    positions *= length_scale
    positions += (1-length_scale)*roots
    data.position_data.foreach_set('vector', positions.ravel())
    radius = data.attributes['radius'].data
    widths = np.empty(len(radius), dtype=np.float32)
    radius.foreach_get('value', widths)
    widths *= radius_scale
    radius.foreach_set('value', widths)
    data.update_tag()

for side in ('L', 'R'):
    eye = bpy.data.objects['GEO-eye.' + side]
    for slot in eye.material_slots:
        source = slot.material.name
        new = bpy.data.materials.get(source + " | portrait")
        if new is None:
            new = material(source + " | portrait", (.018,.013,.010), .25)
            shader = new.node_tree.nodes.get('Principled BSDF')
            if 'pupil' not in source:
                tex = image_texture(new.node_tree, 'eyes.albedo')
                new.node_tree.links.new(tex.outputs['Color'], shader.inputs['Base Color'])
            shader.inputs['Coat Weight'].default_value = .15
        slot.material = new
tint_shader(bpy.data.materials['einar.hat'].node_tree, (.51,.66,.70), .83)

position_keys('FK-Head', [
    (1, (-.035, -.025, -.035)), (16, (-.035, -.025, -.035)),
    (22, (.001, .042, -.03)), (31, (.072, .125, -.021)),
    (40, (.082, .116, -.022)), (48, (.082, .116, -.022)),
], 'rotation_euler')
position_keys('MSTR-TGT-Eyes', [
    (1, (-.055, .0, .025)), (13, (-.055, .0, .025)),
    (16, (-.59, -.01, .035)), (21, (-.63, -.01, -.014)),
    (28, (-.66, -.01, -.16)), (33, (-.68, -.01, -.24)),
    (38, (-.54, -.01, -.16)), (48, (-.54, -.01, -.13)),
])
position_keys('FK-Chest', [(f, (x, 0, 0)) for f, x in
    [(1, -.019), (13, -.023), (27, -.018), (40, -.023), (48, -.022)]],
    'rotation_euler')
for side, sign in [('L', 1), ('R', -1)]:
    position_keys('ACT-Eyebrow_Inner.' + side,
                  [(1, (-sign*.0015, -.0029, 0)), (18, (-sign*.0015, -.0027, 0)),
                   (31, (-sign*.001, -.0029, 0)), (43, (-sign*.0008, -.0019, 0))])
    position_keys('ACT-Mouth_Corner.' + side,
                  [(1, (-sign*.0013, -.0016, 0)), (32, (-sign*.0013, -.0016, 0)),
                   (39, (-sign*.00035, -.00055, 0)), (48, (-sign*.00035, -.00055, 0))])
    for lid in ('Blink.', 'Eyelid_Upper.'):
        resting = .0016 if lid == 'Eyelid_Upper.' else 0
        closed = -.006 if lid == 'Eyelid_Upper.' else -.0037
        position_keys(lid + side,
                      [(1, (0, resting, 0)), (33, (0, resting, 0)),
                       (34, (0, closed, 0)), (35, (0, closed*.46, 0)),
                       (36.4, (0, resting, 0)), (48, (0, resting, 0))])

camera_data = bpy.data.cameras.new("Portrait lens")
camera = bpy.data.objects.new("Locked three-quarter close-up", camera_data)
scene.collection.objects.link(camera)
camera.location = (.53, -1.20, 1.19)
point_at(camera, (.038, -.025, 1.003))
camera_data.lens = 69
camera_data.dof.use_dof = True
camera_data.dof.focus_distance = (camera.location - Vector((0, -.121, 1.025))).length
camera_data.dof.aperture_fstop = 5.6
scene.camera = camera

# Fluted, slightly leaning oak. UVs tile the photographs along the grain.
bark = material("Oak | fissured bark", (.19, .11, .067))
tree = bark.node_tree
bs = tree.nodes.get('Principled BSDF')
for name, filename in [('Color', 'oak_bark_diffuse.jpg'), ('Normal', 'oak_bark_normal.jpg')]:
    tex = tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(ENV / filename))
    if name == 'Normal':
        tex.image.colorspace_settings.name = 'Non-Color'
        normal = tree.nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value = .85
        tree.links.new(tex.outputs['Color'], normal.inputs['Color'])
        tree.links.new(normal.outputs['Normal'], bs.inputs['Normal'])
    else:
        tree.links.new(tex.outputs['Color'], bs.inputs['Base Color'])

verts, faces = [], []
rings, sides = 30, 112
for j in range(rings):
    z = j * .095 - .18
    for i in range(sides + 1):
        a = 2*pi*i/sides
        r = .361 + .105*exp(-max(z, 0)*8) - max(z, 0)*.016
        r += .019*sin(7*a+.72*z) + .012*cos(17*a-1.1*z) + .007*sin(37*a+2*z)
        verts.append((-.456 + .041*z + r*cos(a), .333 + .021*z + r*sin(a), z))
        if j and i:
            k = j*(sides+1)+i
            faces.append((k-sides-2, k-sides-1, k, k-1))
trunk = mesh("Oak at the field edge", verts, faces, [bark])
uv = trunk.data.uv_layers.new()
for poly in trunk.data.polygons:
    poly.use_smooth = True
    for li in poly.loop_indices:
        j, i = divmod(trunk.data.loops[li].vertex_index, sides+1)
        uv.data[li].uv = (2.25*i/sides, j*.095*.88)

soil = material("Meadow floor", (.18, .205, .073))
nt = soil.node_tree
noise = nt.nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 1.6
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .19
ramp.color_ramp.elements[0].color = (.067, .079, .029, 1)
ramp.color_ramp.elements[1].position = .82
ramp.color_ramp.elements[1].color = (.34, .32, .106, 1)
nt.links.new(noise.outputs['Fac'], ramp.inputs[0])
nt.links.new(ramp.outputs['Color'], nt.nodes.get('Principled BSDF').inputs['Base Color'])


def ground_z(x, y):
    return .10*sin(x*.47)*sin(y*.32) + .08*sin(y*.65) + .46*exp(-((y-14)/6)**2)


verts = [(x*.7, y*.7, ground_z(x*.7, y*.7))
         for y in range(-8, 47) for x in range(-45, 34)]
faces = [(i, i+1, i+80, i+79) for i in range(len(verts)-79) if i%79 < 78]
ground = mesh("Rolling field", verts, faces, [soil])
for face in ground.data.polygons:
    face.use_smooth = True

grass_colors = [(.19,.23,.059), (.30,.32,.090), (.42,.37,.122),
                (.26,.30,.086), (.48,.40,.18), (.15,.20,.059)]
grass_mats = [material("Field blade %s" % i, col) for i, col in enumerate(grass_colors)]
for mat in grass_mats:
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Subsurface Weight'].default_value = .14

# Root-locked blade shapes. A traveling pressure pulse drives each strip
# in succession, with a slower recovery and a staggered secondary sway.
for row in range(14):
    verts, faces, indices, flex = [], [], [], []
    for clump in range(130):
        x = rng.uniform(-12, 5)
        y = rng.uniform(.45 + row*.7, 1.15 + row*.7)
        if (x+.28)**2 + (y-.42)**2 < .55**2:
            continue
        for blade in range(rng.randint(5, 10)):
            bx = x + rng.gauss(0, .095)
            by = y + rng.gauss(0, .08)
            bz = ground_z(bx, by)
            h = rng.uniform(.19, .70)
            if row < 4:
                h *= rng.uniform(1, 1.54)
            a = rng.uniform(0, 2*pi)
            w = rng.uniform(.007, .023)
            lean = rng.uniform(.06, .22)
            phase = rng.uniform(.65, 1.35)
            start = len(verts)
            for t in (0, .34, .68, 1):
                for edge in (-1, 1):
                    width = edge*w*(1-.97*t)
                    verts.append((bx + lean*t*t*cos(a) - width*sin(a),
                                  by + lean*t*t*sin(a) + width*cos(a),
                                  bz+h*t-.06*t*t))
                    flex.append(h*t*t*phase)
            faces.extend([(start+i, start+i+1, start+i+3, start+i+2) for i in (0, 2, 4)])
            indices.extend([rng.randrange(len(grass_mats))]*3)
    patch = mesh("Grass wave strip %02d" % row, verts, faces, grass_mats, indices)
    patch.shape_key_add(name="Upright")
    bend = patch.shape_key_add(name="Downwind flex")
    for v, weight in zip(bend.data, flex):
        v.co.x += weight*.46
        v.co.y += weight*.19
        v.co.z -= weight*.19
    for frame in range(1, 49, 2):
        t = (frame-1)/12 - row*.039
        envelope = exp(-((t-1.79)/.71)**4)
        bend.value = .025 + envelope*(.53 + .32*sin(9*t-row*.33))
        bend.keyframe_insert(data_path="value", frame=frame)

# Low trees on the far ridge use irregular, overlapping crowns.
woods = [material("Hedgerow %d" % i, col) for i, col in enumerate(
    [(.11,.15,.069), (.18,.20,.081), (.24,.24,.105), (.33,.27,.106)])]
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1)
template = bpy.context.object
crown_vertices = [v.co.copy() for v in template.data.vertices]
crown_faces = [tuple(p.vertices) for p in template.data.polygons]
bpy.data.objects.remove(template, do_unlink=True)
verts, faces, indices = [], [], []
for i in range(64):
    x = rng.uniform(-31, 15)
    y = rng.uniform(14, 24)
    height = rng.uniform(.5, 1.85)
    for j in range(3):
        px, py = x+rng.uniform(-.7,.7), y+rng.uniform(-.6,.6)
        pz = ground_z(x,y)+height*.58
        sx, sy, sz = rng.uniform(.4,1.1), rng.uniform(.45,.9), height*rng.uniform(.45,.86)
        offset = len(verts)
        verts.extend((px+vx*sx, py+vy*sy, pz+vz*sz) for vx,vy,vz in crown_vertices)
        faces.extend(tuple(offset+k for k in face) for face in crown_faces)
        indices.extend([rng.randrange(len(woods))]*len(crown_faces))
hedgerow = mesh("Distant hedgerow", verts, faces, woods, indices)
for poly in hedgerow.data.polygons:
    poly.use_smooth = True

world = bpy.data.worlds.new("Open sky above the meadow")
scene.world = world
world.use_nodes = True
nt = world.node_tree
background = nt.nodes.get('Background')
background.inputs['Color'].default_value = (.47, .61, .76, 1)
background.inputs['Strength'].default_value = .42


def light(name, kind, xyz, aim, power, color, size):
    data = bpy.data.lights.new(name, kind)
    data.energy = power
    data.color = color
    if kind == 'AREA':
        data.shape = 'DISK'
        data.size = size
    else:
        data.angle = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = xyz
    point_at(obj, aim)


light("Low afternoon sun", 'SUN', (2, 3, 3.15), (0, 0, 0), 2.15, (1, .79, .54), .16)
light("Open sky reflected into shade", 'AREA', (.08, -2.3, 2.72), (0, 0, 1.04), 99,
      (.86, .92, 1), 2.1)
light("Warm field bounce", 'AREA', (1.4, .35, .78), (0, 0, 1.03), 29,
      (1, .85, .64), 1.5)

# Place leaf trajectories in view space at fixed physical depths, then
# keyframe the resulting world positions. The featured leaf falls beside him.
bpy.context.view_layer.update()
view_frame = camera_data.view_frame(scene=scene)


def in_view(u, v, depth):
    x = min(p.x for p in view_frame) + u*(max(p.x for p in view_frame)-min(p.x for p in view_frame))
    y = min(p.y for p in view_frame) + v*(max(p.y for p in view_frame)-min(p.y for p in view_frame))
    local = Vector((x, y, view_frame[0].z))
    return camera.matrix_world @ (local * (-depth/local.z))


leaf_mats = [material("Oak leaf | "+name, col, .48) for name, col in [
    ('gold', (.65,.27,.041)), ('ochre', (.46,.155,.026)),
    ('olive', (.26,.27,.047)), ('pale underside', (.48,.33,.107)),
    ('vein', (.36,.20,.059))]]
for mat in leaf_mats:
    mat.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value = .08


def oak_leaf(name, length, index):
    verts, faces, ids = [], [], []
    outline = [0, .13, .37, .30, .48, .37, .50, .35, .43, .23, .31, .12, 0]
    for i, width in enumerate(outline):
        t = i/(len(outline)-1)
        for side in (-1, 0, 1):
            verts.append((side*length*width*.75, length*(t-.49),
                          length*(.15*(t-.45)**2 + abs(side)*width*.19)))
    for i in range(12):
        for j in range(2):
            a = i*3+j
            faces.append((a, a+1, a+4, a+3))
            ids.append(index)
        a = len(verts)
        y = length*(i/12-.49)
        width = length*.014*(1-i/13)
        verts.extend([(-width,y, length*(.15*(i/12-.45)**2+.004)),
                      (width,y, length*(.15*(i/12-.45)**2+.004)),
                      (0,y+length*.111, length*(.15*((i+1)/12-.45)**2+.004))])
        faces.append((a,a+1,a+2))
        ids.append(4)
    obj = mesh(name, verts, faces, leaf_mats, ids)
    solid = obj.modifiers.new("Leaf thickness", 'SOLIDIFY')
    solid.thickness = .00032
    return obj


for i, (start, duration, u, drift, depth, length) in enumerate([
    (12.8, 29, .727, .14, .83, .036),
    (16, 39, .96, -.07, 2.10, .058),
    (10, 28, .085, .06, 1.91, .042),
    (20, 34, .86, .05, 2.48, .064),
    (27, 34, .989, -.14, 1.77, .035),
    (30, 35, .72, .11, 2.25, .046),
]):
    obj = oak_leaf("Falling leaf %02d" % (i+1), length, i%3)
    for frame in range(1, 49):
        t = (frame-start)/duration
        phase = (frame-start)*(.29+.034*i) + i*.7
        if i == 0:
            height = .94 - .91*t - .13*(1-exp(-11*t)) if t >= 0 else .94 - 2.34*t
        else:
            height = 1.13 - 1.14*t
        obj.location = in_view(u + drift*t + .022*sin(phase),
                               height + .018*cos(phase), depth+.071*sin(phase*.63))
        obj.rotation_euler = (1.18+.64*sin(phase), .53*cos(phase*.82), -.50 + phase*.62)
        obj.keyframe_insert(data_path="location", frame=frame)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)

for name, frame in [('Hold in shade', 1), ('Breeze and first glance', 13),
                    ('Head follows', 18), ('Breeze falls away', 32), ('Blink', 34),
                    ('Hold the release', 41)]:
    scene.timeline_markers.new(name, frame=frame)
scene.frame_set(1)
