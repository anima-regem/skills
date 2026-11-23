"""A quiet riverbank, in metres, sampled at 12 fps.

The watcher's weight is supported by two planted feet on the dry terrace.
The head picks up a patch of surface streaks, follows it, and settles downstream.
A shallow, gently sloping channel is implied by its exposed gravel margins.
Flow speeds are estimates, stylized as moving ribbons and shader detail.
Bank drag informs the cross-channel speed profile (USGS Circular 1246).
No props obstruct the active channel and the watcher stays above the waterline.
"""
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start, scene.frame_end = 1, 48
scene.unit_settings.system = 'METRIC'
scene.view_settings.view_transform = 'AgX'
rng = random.Random(605)


def material(name, rgb, roughness=.85, emission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Emission Color'].default_value = (*rgb, 1)
    bsdf.inputs['Emission Strength'].default_value = emission
    return mat


def mesh(name, vertices, faces, materials):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    for mat in materials:
        data.materials.append(mat)
    return ob


def look_at(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()


def near(x):
    return -2.15 + .43 * math.sin(.34 * x + .4) + .19 * math.sin(.73 * x)


def far(x):
    return 3.3 + .61 * math.sin(.29 * x + 1.2) + .23 * math.sin(.59 * x)


sand = [material('Ochre topsoil', (.38, .25, .115)),
        material('Sunlit silt', (.43, .30, .155)),
        material('Dry sand', (.48, .35, .19)),
        material('Wet clay', (.24, .165, .095)),
        material('Shallows gravel', (.14, .18, .13))]
meadow = [material('Olive meadow', (.20, .24, .092)),
          material('Dried meadow', (.24, .265, .105)),
          material('Sage meadow', (.17, .21, .09))]
stones = [material('Basalt', (.15, .16, .14)),
          material('Limestone', (.37, .34, .24)),
          material('Slate', (.21, .25, .21))]
reeds = [material('Rush gold', (.46, .34, .10)),
         material('Rush olive', (.24, .29, .10)),
         material('Rush straw', (.55, .43, .18))]

# The two submerged toes overlap the water mesh. The dry terrace is level
# across the character's whole footprint.
for edge, sign in ((near, -1), (far, 1)):
    sections = [(-.30, -.18), (0, 0), (.18, .10), (.48, .33),
                (.85, .43), (1.55, .43), (2.6, .46), (4, .54),
                (7, .68), (15, .75)]
    verts = []
    for i in range(101):
        x = -30 + i * .6
        for j, (offset, height) in enumerate(sections):
            texture = .10 * math.sin(x * .55 + j) if j >= 6 else 0
            verts.append((x, edge(x) + sign * offset, height + texture))
    width = len(sections)
    faces = [(i*width+j, (i+1)*width+j, (i+1)*width+j+1, i*width+j+1)
             for i in range(100) for j in range(width-1)]
    if sign == -1:
        faces = [f[::-1] for f in faces]
    bank = mesh('Near bank' if sign == -1 else 'Far bank', verts, faces, sand + meadow)
    for i, poly in enumerate(bank.data.polygons):
        j = i % (width - 1)
        poly.material_index = [4, 3, 3, 2, 2, 1, 0, 5, 5][j]
        if j >= 7 and rng.random() < .32:
            poly.material_index = rng.choice((6, 7))
        if j == 5 and rng.random() < .12:
            poly.material_index = 2

water = material('River | moving silk', (.026, .22, .25), .29, .12)
nt = water.node_tree
nd = nt.nodes
link = nt.links.new
bsdf = nd.get('Principled BSDF')
coord = nd.new('ShaderNodeTexCoord')
mapping = nd.new('ShaderNodeVectorMath')
mapping.operation = 'ADD'
link(coord.outputs['Object'], mapping.inputs[0])
motion = mapping.inputs[1].driver_add('default_value', 0)
motion.driver.expression = '-(frame-1)*0.095'
stretch = nd.new('ShaderNodeVectorMath')
stretch.operation = 'MULTIPLY'
stretch.inputs[1].default_value = (.42, 2.75, 1)
link(mapping.outputs[0], stretch.inputs[0])
noise = nd.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 2.3
noise.inputs['Detail'].default_value = 2
link(stretch.outputs[0], noise.inputs['Vector'])
palette = nd.new('ShaderNodeValToRGB')
for point, pos, col in zip(palette.color_ramp.elements, (.22, .80),
                           ((.019, .135, .18, 1), (.063, .31, .34, 1))):
    point.position, point.color = pos, col
link(noise.outputs['Fac'], palette.inputs[0])
link(palette.outputs[0], bsdf.inputs['Base Color'])
link(palette.outputs[0], bsdf.inputs['Emission Color'])
bump = nd.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .19
bump.inputs['Distance'].default_value = .045
link(noise.outputs['Fac'], bump.inputs['Height'])
link(bump.outputs[0], bsdf.inputs['Normal'])
river_verts = [(x, edge(x) + pad, .004)
               for x in [-30 + i*.6 for i in range(101)]
               for edge, pad in ((near, -.14), (far, .14))]
mesh('River surface', river_verts,
     [(2*i, 2*i+2, 2*i+3, 2*i+1) for i in range(100)], [water])

glints = [material('Water | jade reflection', (.095, .37, .38), .46, .34),
          material('Water | mint reflection', (.20, .55, .51), .48, .44),
          material('Water | pale reflection', (.42, .72, .66), .5, .53)]
# Sparse tapered marks advect continuously in +X. Their paths bend with
# the shoreline and run at about 0.45 m/s at the edges and 1.5 m/s midstream.
for i in range(215):
    x0 = rng.uniform(-21, 17)
    lane = rng.uniform(.022, .976)
    speed = .36 + 1.16 * math.sin(math.pi * lane)**.73
    length = rng.uniform(.17, .93) * (.63 + .39 * speed)
    width = rng.uniform(.012, .044)
    phase = rng.uniform(0, math.tau)
    vertices = []
    for j in range(9):
        s = j / 8
        taper = .035 + .965 * math.sin(math.pi * s)**.75
        y = .031 * math.sin(s * 4.5 + phase)
        vertices.extend(((length * (s - .5), y - width * taper, 0),
                         (length * (s - .5), y + width * taper, 0)))
    mark = mesh('Advected surface reflection', vertices,
                [(2*j, 2*j+2, 2*j+3, 2*j+1) for j in range(8)],
                [rng.choices(glints, (7, 4, 1))[0]])
    for frame in (*range(1, 48, 2), 48):
        t = (frame - 1) / 12
        x = x0 + speed * t
        y = (1-lane)*near(x) + lane*far(x)
        mark.location = (x, y + .027 * math.sin(phase + 1.9*t), .014 + .0002*(i % 6))
        slope = (1-lane)*(near(x+.1)-near(x-.1)) + lane*(far(x+.1)-far(x-.1))
        mark.rotation_euler.z = math.atan2(slope, .2)
        mark.scale = (1 + .16*math.sin(phase+2*t),
                      .80 + .19*math.sin(phase+2.7*t), 1)
        for prop in ('location', 'rotation_euler', 'scale'):
            mark.keyframe_insert(prop, frame=frame)
    for curve in mark.animation_data.action.layers[0].strips[0].channelbag(
            mark.animation_data.action_slot).fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'

watch_x = -1.9
watch_y = near(watch_x) - 1.11
for i in range(125):
    edge, sign = rng.choice(((near, -1), (far, 1)))
    x = rng.uniform(-16, 17)
    offset = rng.uniform(.04, 2.85)
    y = edge(x) + sign*offset
    if math.hypot(x-watch_x, y-watch_y) < .75:
        continue
    z = min(.43, offset*.59)
    size = rng.uniform(.043, .17) * (1.6 if i % 9 == 0 else 1)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=size,
                                        location=(x, y, z))
    rock = bpy.context.object
    rock.name = 'Shore pebble'
    rock.rotation_euler.z = rng.uniform(0, math.tau)
    rock.scale = (rng.uniform(1.0, 1.6), rng.uniform(.7, 1.2), rng.uniform(.40, .72))
    rock.data.materials.append(rng.choice(stones))

for edge, sign in ((near, -1), (far, 1)):
    vertices, faces, indices = [], [], []
    for i in range(150):
        x = rng.uniform(-18, 18)
        offset = rng.choice((rng.uniform(.49, .75), rng.uniform(1.85, 3.7)))
        y = edge(x) + sign*offset
        if math.hypot(x-watch_x, y-watch_y) < .85:
            continue
        for j in range(rng.randint(3, 8)):
            px = x + rng.uniform(-.15, .15)
            py = y + rng.uniform(-.10, .10)
            z = max(.25, min(.43, offset * .58)) - .02
            length = rng.uniform(.10, .46) * (1.28 if sign > 0 else 1)
            angle = rng.uniform(0, math.tau)
            dx, dy = math.cos(angle), math.sin(angle)
            w = rng.uniform(.011, .025)
            a = len(vertices)
            vertices.extend(((px-dy*w, py+dx*w, z), (px+dy*w, py-dx*w, z),
                             (px+.22*dx*length, py+.22*dy*length, z+length*.62),
                             (px+.57*dx*length, py+.57*dy*length, z+length)))
            faces.extend(((a, a+1, a+2), (a, a+2, a+3)))
            indices.extend([rng.randrange(len(reeds))]*2)
    grass = mesh('Bank rushes', vertices, faces, reeds)
    for poly, index in zip(grass.data.polygons, indices):
        poly.material_index = index

# Sample a relaxed stance from the supplied skin and pin its lower body.
# Authored head poses keep the line of sight on a downstream path.
bpy.ops.import_scene.gltf(filepath=str(Path(__file__).resolve().parent / 'assets/watcher.glb'))
rig = next(ob for ob in bpy.context.selected_objects if ob.type == 'ARMATURE')
root = rig
while root.parent:
    root = root.parent
body = bpy.data.objects['SuperHero_Male']
scene.frame_set(17)
bpy.context.view_layer.update()
stance = {bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones}
rig.animation_data_clear()
for bone in rig.pose.bones:
    bone.matrix_basis = stance[bone.name]
root.matrix_world = (Matrix.Translation((watch_x, watch_y, 0)) @
                     Matrix.Rotation(math.radians(129), 4, 'Z') @ root.matrix_world)
bpy.context.view_layer.update()
evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
sole = min((evaluated.matrix_world @ v.co).z for v in evaluated.data.vertices)
root.location.z += .431 - sole
bpy.context.view_layer.update()

# Clay-figure palette, with two matte garment tones assigned on the rest mesh.
jacket = material('Watcher | vermilion jacket', (.58, .105, .043), .73)
pants = material('Watcher | charcoal trousers', (.040, .059, .068), .83)
skin = material('Watcher | warm clay', (.50, .28, .17), .70)
boots = material('Watcher | leather boots', (.075, .043, .034))
body.data.materials.clear()
for mat in (jacket, pants, skin, boots):
    body.data.materials.append(mat)
for poly in body.data.polygons:
    weights = {}
    for vi in poly.vertices:
        for group in body.data.vertices[vi].groups:
            name = body.vertex_groups[group.group].name.lower()
            weights[name] = weights.get(name, 0) + group.weight
    dominant = max(weights, key=weights.get, default='')
    if dominant.startswith(('foot', 'ball', 'toe')):
        poly.material_index = 3
    elif dominant.startswith(('pelvis', 'thigh', 'calf')):
        poly.material_index = 1
    elif dominant.startswith(('head', 'neck', 'hand', 'thumb', 'index', 'middle', 'ring', 'pinky')):
        poly.material_index = 2
    else:
        poly.material_index = 0

head = rig.pose.bones['Head']
base = head.matrix.copy()
head.rotation_mode = 'QUATERNION'
world_axes = rig.matrix_world.inverted().to_3x3()
jaw_axis = world_axes @ Vector((-.63, .78, 0))
vertical = world_axes @ Vector((0, 0, 1))
for frame, yaw, dip in ((1, 38, 23), (8, 38, 28), (19, 24, 26),
                        (33, 8, 21), (42, 4, 19), (48, 5, 19)):
    turn = Matrix.Rotation(math.radians(yaw), 4, vertical)
    bend = Matrix.Rotation(math.radians(dip), 4, jaw_axis)
    head.matrix = Matrix.Translation(base.translation) @ turn @ bend @ (
        Matrix.Translation(-base.translation) @ base)
    head.keyframe_insert('rotation_quaternion', frame=frame, group='Follow the current')

bpy.ops.object.camera_add(location=(5.15, -10.6, 7.1))
camera = bpy.context.object
camera.name = 'Riverbank view'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 10.7
look_at(camera, (-.18, -.50, .35))
scene.camera = camera

world = bpy.data.worlds.new('Pale sky')
world.use_nodes = True
world.node_tree.nodes.get('Background').inputs[0].default_value = (.46, .59, .74, 1)
world.node_tree.nodes.get('Background').inputs[1].default_value = .42
scene.world = world
bpy.ops.object.light_add(type='SUN', location=(-5, -6, 8))
sun = bpy.context.object
sun.name = 'Late afternoon sun'
sun.data.color = (1, .81, .59)
sun.data.energy = 2.35
sun.data.angle = math.radians(11)
look_at(sun, (0, 0, 0))
bpy.ops.object.light_add(type='AREA', location=(1, 2, 7))
fill = bpy.context.object
fill.name = 'Open sky fill'
fill.data.energy = 380
fill.data.shape = 'DISK'
fill.data.size = 8
fill.data.color = (.65, .82, 1)
look_at(fill, (0, -1, 0))

scene.frame_set(1)
