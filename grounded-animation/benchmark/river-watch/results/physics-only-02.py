"""Four seconds on a quiet bend. Run with Blender in background mode."""
import math
import random

import bpy
from mathutils import Vector

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
world = bpy.data.worlds.new('Blue skylight')
scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.44, .58, .7, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .35
rng = random.Random(43)


def material(name, rgb, roughness=.8, glow=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*rgb, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Emission Color'].default_value = (*rgb, 1)
    shader.inputs['Emission Strength'].default_value = glow
    return mat


def mesh(name, verts, faces, mat, parent=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj


def pivot(name, pos, parent=None):
    obj = bpy.data.objects.new(name, None)
    scene.collection.objects.link(obj)
    obj.parent = parent
    obj.location = pos
    return obj


def oval(name, pos, scale, mat, parent=None, faceted=False):
    if faceted:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12)
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.location = pos
    obj.scale = scale
    obj.data.materials.append(mat)
    if not faceted:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def segment(name, a, b, width, depth, mat, parent):
    delta = Vector(b) - Vector(a)
    obj = oval(name, (Vector(a) + Vector(b)) / 2,
               (width, depth, delta.length / 2 + width * .62), mat, parent)
    obj.rotation_euler = delta.to_track_quat('Z', 'Y').to_euler()
    return obj


def rings(name, sections, mat, parent):
    n = 24
    verts = [(rx * math.cos(i * math.tau / n), y + ry * math.sin(i * math.tau / n), z)
             for z, y, rx, ry in sections for i in range(n)]
    faces = [tuple(reversed(range(n)))]
    for j in range(len(sections) - 1):
        for i in range(n):
            a, b = j * n + i, j * n + (i + 1) % n
            faces.append((a, b, b + n, a + n))
    faces.append(tuple(range(len(verts) - n, len(verts))))
    obj = mesh(name, verts, faces, mat, parent)
    for poly in obj.data.polygons:
        poly.use_smooth = len(poly.vertices) == 4
    return obj


coat = material('Persimmon wool', (.56, .064, .032))
seam = material('Dark terracotta knit', (.28, .032, .022))
scarf = material('Oatmeal knit', (.79, .59, .32))
skin = material('Warm clay', (.55, .26, .135))
hair = material('Dark walnut', (.055, .025, .020))
ink = material('Midnight blue', (.034, .072, .091))
boot = material('Boot leather', (.043, .032, .030))
sole = material('Rubber soles', (.023, .023, .021))
eye = material('Eye', (.027, .017, .014))

# Metre-scale figure. Both soles stay on the terrace through all poses.
watcher = pivot('Watcher · planted stance', (-2.15, -3.34, .42))
watcher.rotation_euler.z = math.radians(-24)
for side in (-1, 1):
    x = side * .118
    y = .05 * side
    oval('Flat boot sole', (x, y + .045, .034), (.086, .158, .037), sole, watcher)
    oval('Leather boot', (x, y + .035, .086), (.083, .148, .077), boot, watcher)
    segment('Trouser leg', (x, y, .12), (side * .105, 0, .85), .085, .093, ink, watcher)

chest = pivot('Weight over both feet', (0, 0, .84), watcher)
rings('Wool coat', [(-.075, 0, .188, .124), (-.049, 0, .204, .133),
                   (.11, -.006, .204, .139), (.29, 0, .222, .144),
                   (.43, 0, .249, .135), (.49, .002, .201, .108),
                   (.535, .012, .105, .089)], coat, chest)
rings('Coat hem', [(-.070, 0, .193, .128), (-.044, 0, .205, .135)], seam, chest)
for side in (-1, 1):
    shoulder = (side * .192, -.001, .42)
    elbow = (side * .268, .018, .22)
    cuff = (side * .208, .112, .095)
    segment('Upper coat sleeve', shoulder, elbow, .089, .086, coat, chest)
    segment('Forearm tucked toward pocket', elbow, cuff, .074, .073, coat, chest)
    oval('Pocket opening', (side * .154, .115, .092), (.074, .027, .036), seam, chest)
    oval('Hand at pocket', (side * .185, .136, .085), (.052, .037, .048), skin, chest)
for z in (.18, .28, .38):
    oval('Horn button', (.026, .143, z), (.014, .011, .014), boot, chest)
oval('Scarf collar', (0, .006, .53), (.134, .116, .075), scarf, chest)
tail = oval('Tucked scarf end', (-.068, .115, .405), (.058, .034, .132), scarf, chest)
tail.rotation_euler.y = -.24
head = pivot('Head · follows floating leaf', (0, .018, .573), chest)
oval('Neck', (0, 0, .019), (.074, .071, .092), skin, head)
oval('Face', (0, .014, .149), (.111, .114, .145), skin, head)
oval('Nose', (0, .126, .136), (.028, .042, .032), skin, head)
for side in (-1, 1):
    oval('Ear', (side * .108, .006, .129), (.026, .033, .045), skin, head)
    oval('Eye', (side * .047, .114, .171), (.017, .010, .011), eye, head)
    oval('Brow', (side * .049, .111, .196), (.023, .009, .007), hair, head)
oval('Hair at nape', (0, -.060, .171), (.112, .070, .104), hair, head)
oval('Moss knit cap', (0, -.011, .245), (.125, .127, .097), ink, head)
rings('Turned cap brim', [(.202, -.005, .117, .115), (.209, -.004, .125, .122),
                         (.237, -.010, .125, .125), (.245, -.010, .122, .122)], ink, head)

# Low-gradient, roughly 6 m wide channel. The bed and banks are fixed.
# Speed, banks and foam shapes are stylized estimates for this shot.
sand = material('Ochre cut bank', (.39, .22, .108))
damp = material('Wet bank', (.23, .16, .088))
grass_edge = material('Sunlit grass edge', (.259, .33, .135))
grass = material('Meadow', (.24, .312, .119))
for surface, color in [(sand, (.39, .22, .108)), (grass, (.24, .312, .119)),
                       (grass_edge, (.259, .33, .135))]:
    tree = surface.node_tree
    coordinates = tree.nodes.new('ShaderNodeTexCoord')
    variation = tree.nodes.new('ShaderNodeTexNoise')
    variation.inputs['Scale'].default_value = 1.35
    variation.inputs['Detail'].default_value = 3
    tree.links.new(coordinates.outputs['Object'], variation.inputs['Vector'])
    shades = tree.nodes.new('ShaderNodeValToRGB')
    shades.color_ramp.elements[0].color = (*(c * .76 for c in color), 1)
    shades.color_ramp.elements[1].color = (*(c * 1.18 for c in color), 1)
    tree.links.new(variation.outputs['Fac'], shades.inputs[0])
    tree.links.new(shades.outputs['Color'],
                   tree.nodes.get('Principled BSDF').inputs['Base Color'])
stone = [material('Slate shade %d' % i, rgb) for i, rgb in enumerate(
    [(.20, .24, .235), (.28, .31, .28), (.35, .34, .276)])]


def edge(x, side):
    return side * (2.28 if side < 0 else 3.72) + .26 * math.sin(x * .43) + .16 * math.sin(x * .89 + .5)


xs = [i * .25 for i in range(-120, 121)]
for side in (-1, 1):
    verts = []
    for x in xs:
        y = edge(x, side)
        verts.extend([(x, y - side * .25, -.28), (x, y, .014),
                      (x, y + side * .22, .12), (x, y + side * .43, .42),
                      (x, y + side * 1.2, .42), (x, y + side * 13, .42)])
    faces = [(i+j, i+j+6, i+j+7, i+j+1) for i in range(0, len(verts)-6, 6) for j in range(5)]
    if side == -1:
        faces = [face[::-1] for face in faces]
    land = mesh('Near terrace' if side < 0 else 'Far terrace', verts, faces, damp)
    for mat in [sand, grass_edge, grass]:
        land.data.materials.append(mat)
    for i, poly in enumerate(land.data.polygons):
        strip = i % 5
        poly.material_index = strip if strip < 2 else (2 if strip == 2 else 3)
    for i in range(57):
        x = rng.uniform(-15, 15)
        y = edge(x, side) + side * rng.uniform(.07, .42)
        size = rng.uniform(.042, .17)
        oval('Waterline gravel', (x, y, .04), (size * 1.6, size, size * .63),
             rng.choice(stone), faceted=True)

water = material('Jade water · advected surface', (.025, .325, .31), .29)
nodes = water.node_tree.nodes
links = water.node_tree.links
tex = nodes.new('ShaderNodeTexCoord')
shift = nodes.new('ShaderNodeVectorMath')
shift.operation = 'SUBTRACT'
links.new(tex.outputs['Object'], shift.inputs[0])
shift.inputs[1].driver_add('default_value', 0).driver.expression = '(frame-1)*0.9/12'
stretch = nodes.new('ShaderNodeVectorMath')
stretch.operation = 'MULTIPLY'
stretch.inputs[1].default_value = (.59, 3.9, 1)
links.new(shift.outputs['Vector'], stretch.inputs[0])
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 2.15
noise.inputs['Detail'].default_value = 2.0
links.new(stretch.outputs['Vector'], noise.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .18
ramp.color_ramp.elements[0].color = (.018, .22, .23, 1)
ramp.color_ramp.elements[1].position = .85
ramp.color_ramp.elements[1].color = (.08, .44, .379, 1)
links.new(noise.outputs['Fac'], ramp.inputs[0])
bsdf = nodes.get('Principled BSDF')
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .19
bump.inputs['Distance'].default_value = .031
links.new(noise.outputs['Fac'], bump.inputs['Height'])
links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
mesh('River surface', [(x, edge(x, s) + s * .045, 0) for x in xs for s in (-1, 1)],
     [(i, i+2, i+3, i+1) for i in range(0, len(xs)*2-2, 2)], water)

foam = [material('Silver current %d' % i, c, .46, .12) for i, c in enumerate(
    [(.12, .46, .421), (.235, .62, .545), (.44, .72, .619), (.61, .82, .718)])]


def ribbon(name, points, width, mat, parent=None):
    verts = []
    for i, (x, y, z) in enumerate(points):
        w = width * (.08 + .92 * math.sin(math.pi * i / (len(points) - 1)) ** .75)
        verts.extend([(x, y - w, z), (x, y + w, z)])
    return mesh(name, verts, [(i, i+2, i+3, i+1) for i in range(0,len(verts)-2,2)], mat, parent)


# Gravity drives positive X. Rough banks slow the outer lanes.
# Each silver mark follows its lane and gently changes shape as it travels.
for i in range(138):
    x = rng.uniform(-15, 13)
    lane = rng.uniform(.055, .945)
    length = rng.uniform(.23, 1.13)
    speed = .35 + 1.12 * math.sin(math.pi * lane) ** .8
    mark = pivot('Drifting surface trace', (x, 0, .012))
    ribbon('Tapered current glint',
           [(length * j / 10, .033 * math.sin(j * .28 + i), 0) for j in range(11)],
           rng.uniform(.009, .026), rng.choices(foam, [5, 5, 3, 1])[0], mark)
    for frame in (1, 48):
        travel = x + speed * (frame - 1) / 12
        y = edge(travel, -1) * (1 - lane) + edge(travel, 1) * lane
        mark.location.x, mark.location.y = travel, y
        mark.keyframe_insert(data_path='location', frame=frame)
    for fc in mark.animation_data.action.layers[0].strips[0].channelbag(
            mark.animation_data.action_slot).fcurves:
        for key in fc.keyframe_points:
            key.interpolation = 'LINEAR'
    mark.driver_add('scale', 0).driver.expression = f'1+0.15*sin(frame*0.145+{i})'

# A partly submerged rock diverts the current. Fixed wake envelope,
# with streaks beginning at its shoulders and opening downstream.
rock_x, rock_y = 3.05, .68
rock = oval('Emergent slate', (rock_x, rock_y, -.035), (.46, .32, .31), stone[0], faceted=True)
rock.rotation_euler.z = -.38
for side in (-1, 1):
    for j in range(3):
        ribbon('Split wake', [(rock_x - .33 + t * (1.47 + j * .26),
                              rock_y + side * (.20 + j * .092 + .39 * (1 - math.exp(-t * 3))),
                              .018) for t in [i / 18 for i in range(19)]],
               .013 + .003 * j, foam[3-j])
    for i in range(5):
        fleck = pivot('Wake fleck', (rock_x, rock_y + side * .57, .022))
        ribbon('Broken wake glint', [(j * .035, side * j * .004, 0) for j in range(9)],
               .016, foam[2], fleck)
        phase = i / 5
        fleck.driver_add('location', 0).driver.expression = f'{rock_x}+2.7*((frame/25+{phase})%1)'
        fleck.driver_add('scale', 0).driver.expression = f'sin(pi*((frame/25+{phase})%1))'
        fleck.driver_add('scale', 1).driver.expression = f'sin(pi*((frame/25+{phase})%1))'

# Buoyancy holds a bright leaf at the surface. It passes the watcher
# in the near lane, clear of the rock. No contact or release occurs.
leaf_mat = material('Golden floating leaf', (.95, .39, .038), .52, .19)
leaf_vein = material('Leaf midrib', (.48, .145, .022))
leaf = pivot('Floating leaf · gaze target', (-4.65, -.91, .029))
mesh('Curled alder leaf',
     [(-.25, 0, .034), (-.085, -.085, .008), (.06, -.076, .004),
      (.22, 0, .025), (.055, .084, .004), (-.098, .079, .009), (0, 0, .022)],
     [(i, (i+1)%6, 6) for i in range(6)], leaf_mat, leaf)
ribbon('Leaf midrib', [(-.22 + .41 * i / 8, 0, .028 + .009 * (1 - i / 8)**4)
                       for i in range(9)], .008, leaf_vein, leaf)
leaf.driver_add('location', 0).driver.expression = '-4.65+(frame-1)*1.29/12'
leaf.driver_add('location', 1).driver.expression = '-0.91+0.075*sin((frame-1)/15)'
leaf.driver_add('location', 2).driver.expression = '.028+.009*sin(frame*.43)'
leaf.driver_add('rotation_euler', 2).driver.expression = '.21*sin(frame*.18)-.22'
leaf.driver_add('rotation_euler', 0).driver.expression = '.12*sin(frame*.39)'
for frame, lean in ((1, .013), (12, .092), (27, .119), (39, .099), (48, .054)):
    target_x = -4.65 + (frame - 1) * 1.29 / 12
    target_y = -.91 + .075 * math.sin((frame - 1) / 15)
    dx, dy = target_x - watcher.location.x, target_y - watcher.location.y
    yaw = -math.atan2(dx, dy) - watcher.rotation_euler.z
    chest.rotation_euler = (-lean, 0, yaw * .27)
    chest.keyframe_insert(data_path='rotation_euler', frame=frame)
    head.rotation_euler = (-math.atan2(1.9, math.hypot(dx, dy)) * .74 + lean, 0, yaw * .73)
    head.keyframe_insert(data_path='rotation_euler', frame=frame)


# Sparse sedge clusters frame the bank without blocking the stance.
reed = [material('Sedge %d' % i, c) for i, c in enumerate(
    [(.13, .23, .072), (.32, .39, .13), (.49, .48, .19)])]
tufts = [(-6.7,-3.15), (-5.3,-3.0), (-4.65,-3.05), (-3.55,-3.17),
         (-.66,-3.0), (.12,-3.12), (1.3,-3.02), (3.4,-3.12),
         (4.7,-3.2), (5.5,-3.18), (-3.6,-5.8), (-3.1,-5.5)]
tufts += [(x, edge(x, 1) + .54 + rng.random() * .65) for x in
          [-11,-9.5,-8,-7.8,-6,-4.8,-3,-2.4,-.5,1.2,2.1,3.8,4.15,5.8,7.4,9]]
for x, y in tufts:
    for k in range(rng.randint(8, 16)):
        dx, dy = rng.uniform(-.18, .18), rng.uniform(-.16, .16)
        h = rng.uniform(.18, .59)
        bend = dx * .9 + .10
        w = rng.uniform(.012, .028)
        blade = mesh('Sedge blade', [(-w,0,0),(w,0,0),(bend*.38+w*.65,dy*.7,h*.55),
                      (bend,dy,h),(bend*.38-w*.65,dy*.7,h*.55)], [(0,1,2,4),(4,2,3)], rng.choice(reed))
        blade.location = (x+dx,y+dy,.4)
        blade.rotation_euler.z = rng.uniform(-.85,.85)
        blade.driver_add('rotation_euler', 1).driver.expression = f'.065*sin(frame*.22+{x+dy*5})'

for x, y, size in [(-4.2,-3.92,.32),(-4.54,-3.86,.2),(-.2,-3.85,.22),
                   (3.7,-3.8,.46),(4.18,-3.74,.3),(-5.4,4.32,.55),(-4.73,4.42,.32),
                   (1.8,4.82,.45),(2.28,4.73,.27),(6.2,4.2,.51)]:
    obj = oval('Bank stone', (x,y,.404), (size*1.23,size*.84,size*.56), rng.choice(stone), faceted=True)
    obj.rotation_euler.z = rng.uniform(-1,1)


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


bpy.ops.object.camera_add(location=(4.3, -10.3, 7.65))
camera = bpy.context.object
camera.name = 'Bank and river · locked camera'
aim(camera, (-.40, .38, .22))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 11.8
scene.camera = camera

bpy.ops.object.light_add(type='SUN', location=(-4, -3, 7))
sun = bpy.context.object
sun.name = 'Low afternoon sun'
sun.data.energy = 2.25
sun.data.color = (1, .83, .66)
sun.data.angle = math.radians(14)
aim(sun, (1, 1, 0))

bpy.ops.object.light_add(type='AREA', location=(1, 4, 7))
fill = bpy.context.object
fill.name = 'Cool sky bounce'
fill.data.energy = 380
fill.data.shape = 'DISK'
fill.data.size = 8
fill.data.color = (.62, .79, 1)
aim(fill, (0, -2, 0))

scene.frame_set(1)
