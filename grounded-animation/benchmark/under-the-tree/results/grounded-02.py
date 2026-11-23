"""Under the Tree. Build with Blender in background mode using --python scene.py.

Adapted face rig: Einar, Blender Foundation, CC BY 4.0.
https://studio.blender.org/characters/einar/v1/
Jolcham Oak Bark and Autumn Meadow: Poly Haven, CC0.
"""
from pathlib import Path
from math import cos, sin, pi, exp
from random import Random
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ENV = ASSETS / "environment"
rng = Random(16)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.eevee.taa_render_samples = 32
scene.frame_start, scene.frame_end = 1, 48
scene.view_settings.view_transform = 'AgX'

with bpy.data.libraries.load(str(ASSETS / "einar.blend"), link=False) as (_, imported):
    imported.collections = ["CH-einar"]
actor = imported.collections[0]
scene.collection.children.link(actor)
actor.name = "Ivo • field surveyor"
rig = bpy.data.objects["RIG-einar"]
rig.animation_data_clear()
# His weight stays against the oak at shoulder height.
sit = bpy.data.objects.new("Seated position", None)
scene.collection.objects.link(sit)
for obj in actor.all_objects:
    if obj.parent is None and not obj.name.startswith("WGT"):
        obj.parent = sit
sit.location.z = -.68

def material(name, color, roughness=.55):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return mat, shader

def tint(mat, color):
    tree = mat.node_tree
    for shader in list(tree.nodes):
        if shader.type != 'BSDF_PRINCIPLED':
            continue
        socket = shader.inputs["Base Color"]
        if socket.is_linked:
            source = socket.links[0].from_socket
            mix = tree.nodes.new("ShaderNodeMixRGB")
            mix.blend_type = 'MULTIPLY'
            mix.inputs[0].default_value = 1
            mix.inputs[2].default_value = (*color, 1)
            tree.links.new(source, mix.inputs[1])
            tree.links.new(mix.outputs[0], socket)
        else:
            socket.default_value = (*color, 1)

for name, color in {
    "einar.jacket.canvas": (.27,.49,.43),
    "einar.jacket.collar": (.27,.49,.43),
    "einar.jacket.rim": (.37,.58,.49),
    "einar.sweater": (.59,.37,.21),
    "einar.hair": (.45,.30,.23),
}.items():
    tint(bpy.data.materials[name], color)
bpy.data.objects["GEO-einar_hat"].hide_render = True

# Preserve the eyelid alignment while giving Ivo his own nose, chin and cheek line.
head = bpy.data.objects["GEO-einar_head"]
identity = head.shape_key_add(name="Ivo facial proportions", from_mix=False)
for point in identity.data:
    x, y, local_z = point.co
    z = local_z + .0544
    nose = exp(-((x-.001)/.019)**2-((z-1.644)/.025)**2) * max(0.,min(1.,(-y-.125)/.036))
    chin = exp(-((z-1.575)/.027)**2) * max(0.,min(1.,(-y-.065)/.05))
    cheek = exp(-((abs(x)-.067)/.031)**2-((z-1.624)/.033)**2)
    point.co = (x*(1-.085*chin+.048*cheek)+.0027*nose,
                y+.011*nose-.006*chin, local_z-.007*chin)
identity.value = 1


def pose(name, channel, keys):
    bone = rig.pose.bones[name]
    for frame, value in keys:
        setattr(bone, channel, value)
        bone.keyframe_insert(data_path=channel, frame=frame, group=name)

pose("FK-Head", "rotation_euler", [
    (1, (.011,.035,-.027)), (13, (.011,.035,-.028)),
    (17, (.010,.036,-.029)), (24, (-.025,.081,-.033)),
    (31, (.038,.097,-.036)), (39, (.044,.090,-.032)),
    (48, (.041,.086,-.031))])
pose("FK-Chest", "rotation_euler", [(1,(.006,0,0)),(13,(.011,0,0)),
    (26,(.005,0,0)),(37,(.009,0,0)),(48,(.007,0,0))])
for side, sign in (("L",1),("R",-1)):
    pose("ACT-Eyebrow_Inner."+side, "location", [(1,(-sign*.0017,-.0026,0)),
        (14,(-sign*.0017,-.0026,0)),(22,(-sign*.0011,-.0011,0)),
        (34,(-sign*.0013,-.0016,0)),(48,(-sign*.001,-.0017,0))])
    pose("Blink."+side, "location", [(1,(0,0,0)),(33,(0,0,0)),
        (35,(0,-.006,0)), (36,(0,-.0036,0)), (38,(0,0,0)),(48,(0,0,0))])
    pose("Eyelid_Upper."+side, "location", [(1,(0,0,0)),(33,(0,0,0)),
        (35,(0,-.006,0)), (36,(0,-.0036,0)), (38,(0,0,0)),(48,(0,0,0))])
    pose("ACT-Mouth_Corner."+side, "location", [(1,(-sign*.0013,.00125,0)),
        (32,(-sign*.0013,.00125,0)), (39,(-sign*.0002,.00025,0)),
        (48,(-sign*.0002,.00025,0))])
pose("MSTR-Jaw", "rotation_euler", [(1,(.009,0,0)),(32,(.009,0,0)),
    (41,(.018,0,0)),(48,(.016,0,0))])
pose("MSTR-TGT-Eyes", "location", [(1,(-.052,0,.016)),(13,(-.052,0,.016)),
    (15,(-.365,0,.155)),(19,(-.388,0,.093)),(24,(-.420,0,-.008)),
    (31,(-.452,0,-.173)),(35,(-.375,0,-.150)),
    (39,(-.239,0,-.086)),(48,(-.224,0,-.068))])

def aim(object, point):
    object.rotation_euler = (Vector(point) - object.location).to_track_quat('-Z','Y').to_euler()

bpy.ops.object.camera_add(location=(.307,-.875,1.035))
camera = bpy.context.object
camera.name = "Portrait from the edge of the shade"
aim(camera, (.032,-.078,.969))
camera.data.lens = 52
camera.data.dof.use_dof = True
focus = bpy.data.objects.new("Near eye plane", None)
scene.collection.objects.link(focus)
focus.location = (.012,-.113,.989)
camera.data.dof.focus_object = focus
camera.data.dof.aperture_fstop = 4.4
scene.camera = camera

world = bpy.data.worlds.new("Meadow sky")
world.use_nodes = True
scene.world = world
nodes = world.node_tree.nodes
links = world.node_tree.links
env = nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(str(ENV / "autumn_meadow_1k.hdr"))
links.new(env.outputs["Color"], nodes["Background"].inputs["Color"])
nodes["Background"].inputs["Strength"].default_value = .37

def light(name, kind, location, target, color, power, size):
    data = bpy.data.lights.new(name, kind)
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)
    data.color = color
    data.energy = power
    if kind == 'AREA':
        data.shape = 'DISK'
        data.size = size
    else:
        data.angle = size

light("Late sun across the field", 'SUN', (-4,3,4), (0,0,0),
      (1,.77,.46), 2.25, .085)
light("Open sky through the branches", 'AREA', (1,-1.55,2.42), (0,0,1),
      (.76,.84,1), 56, 2.1)
light("Warm meadow bounce", 'AREA', (-.9,-1.1,.75), (0,0,1),
      (1,.82,.64), 14, 1.35)
light("Sun on the field-side edge", 'AREA', (.75,1.25,1.62), (0,0,1),
      (1,.66,.35), 64, .72)

def mesh(name, vertices, polygons, mats):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], polygons)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    for mat in mats:
        data.materials.append(mat)
    return obj

bark, bs = material("Jolcham oak", (.16,.105,.060), .88)
for filename, space in (("oak_bark_diffuse.jpg", 'sRGB'), ("oak_bark_normal.jpg", 'Non-Color')):
    tex = bark.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(ENV / filename))
    tex.image.colorspace_settings.name = space
    if space == 'sRGB':
        bark.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    else:
        normal = bark.node_tree.nodes.new("ShaderNodeNormalMap")
        normal.inputs["Strength"].default_value = 1.25
        bark.node_tree.links.new(tex.outputs["Color"],normal.inputs["Color"])
        bark.node_tree.links.new(normal.outputs["Normal"],bs.inputs["Normal"])

def trunk(name, rings):
    verts, faces = [], []
    sides = 72
    for j,(x,y,z,r) in enumerate(rings):
        for i in range(sides):
            a = i*2*pi/sides
            radius = r*(1+.067*sin(7*a+z*1.3)+.038*sin(21*a-z)+.031*sin(3*a+z*2))
            verts.append((x+radius*cos(a),y+radius*sin(a),z+.021*sin(a*3+z)))
        if j:
            for i in range(sides):
                faces.append(((j-1)*sides+i,(j-1)*sides+(i+1)%sides,
                              j*sides+(i+1)%sides,j*sides+i))
    oak = mesh(name, verts, faces, [bark])
    uv = oak.data.uv_layers.new().data
    for poly in oak.data.polygons:
        j,i = divmod(poly.index,sides)
        z0,z1 = rings[j][2],rings[j+1][2]
        for loop, coord in zip(poly.loop_indices, [(i/sides*2.2,z0*1.05),
              ((i+1)/sides*2.2,z0*1.05),((i+1)/sides*2.2,z1*1.05),(i/sides*2.2,z1*1.05)]):
            uv[loop].uv = coord
        poly.use_smooth = True

trunk("Oak • main stem", [(-.35+.019*sin(z*3),.31+.019*sin(z*4),z,
      .31+.14*exp(-max(z,0)*5)+.013*sin(z*4)) for z in [i*.075-.15 for i in range(80)]])
trunk("Oak • branching stem", [(-.47-.25*t,.33+.34*t,1.55+t,.18-.10*t)
      for t in [i*.1 for i in range(14)]])

ground, shader = material("Meadow earth and moss", (.14,.16,.046), .95)
gn = ground.node_tree.nodes
gl = ground.node_tree.links
coords = gn.new('ShaderNodeTexCoord')
noise = gn.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 2.9
gl.new(coords.outputs['Object'],noise.inputs['Vector'])
ramp = gn.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .22
ramp.color_ramp.elements[0].color = (.066,.080,.024,1)
ramp.color_ramp.elements[1].position = .8
ramp.color_ramp.elements[1].color = (.28,.27,.073,1)
gl.new(noise.outputs['Fac'],ramp.inputs[0])
gl.new(ramp.outputs['Color'],shader.inputs['Base Color'])

def ground_z(x,y):
    return -.07 + .023*sin(x*.7+y*.5) + .34*exp(-((y-9)/4.8)**2) + .19*exp(-((y-22)/8)**2)

vertices = [(x*.65,y*.65,ground_z(x*.65,y*.65))
            for y in range(-8,70) for x in range(-55,56)]
faces = [(i,i+1,i+112,i+111) for i in range(len(vertices)-111) if (i+1)%111]
meadow = mesh("Rising meadow", vertices, faces,[ground])
for p in meadow.data.polygons:
    p.use_smooth = True

def breeze(t, delay):
    u = max(0., t-1.0-delay)
    return (1-exp(-u*7))*exp(-1.7*max(0,t-2.12-delay))

# Deform the distributed blades in spatial bands. Roots stay fixed.
grasses = [material("Meadow blade %d"%i,c,.77)[0] for i,c in enumerate([
    (.25,.28,.055),(.37,.36,.085),(.17,.24,.047),(.49,.39,.117),
    (.29,.31,.080),(.52,.47,.19)])]
for band in range(9):
    verts, faces, indices, weights = [], [], [], []
    for j in range(350):
        y = rng.uniform(.65,13.8)
        if j < 190:
            y = rng.uniform(.75,4.7)
        # Contiguous strips across the visible field carry the gust sideways.
        spacing = .23 + .039*y
        x = -.32*y + (band-3.6)*spacing + rng.uniform(-.57,.57)*spacing
        for _ in range(rng.randint(3,6)):
            xx, yy = x+rng.uniform(-.082,.082),y+rng.uniform(-.082,.082)
            z = ground_z(xx,yy)
            h = rng.uniform(.11,.42)*(1+max(0.,y-4)*.07)
            a = rng.uniform(0,2*pi)
            dx,dy = cos(a),sin(a)
            w = rng.uniform(.006,.018)
            lean = rng.uniform(.12,.52)*h
            start = len(verts)
            for level in (0,.33,.68,1.):
                cx,cy = xx+dx*lean*level**2,yy+dy*lean*level**2
                for sign in (-1,1):
                    width = sign*w*(1-.97*level)
                    verts.append((cx-dy*width,cy+dx*width,z+h*level))
                    weights.append(h*level**2)
            color = rng.randrange(len(grasses))
            for k in range(0,6,2):
                faces.append((start+k,start+k+1,start+k+3,start+k+2))
                indices.append(color)
    grass = mesh("Meadow wind band %d"%band,verts,faces,grasses)
    for poly, idx in zip(grass.data.polygons,indices):
        poly.material_index = idx
    grass.shape_key_add(name="Rooted blades")
    gust = grass.shape_key_add(name="Wind bend")
    for point,(x,y,z),weight in zip(gust.data,verts,weights):
        point.co = (x+.66*weight,y+.27*weight,z-.26*weight)
    for f in range(1,49,2):
        t = (f-1)/12
        delay = band*.067
        gust.value = .05 + breeze(t,delay)*(.5+.39*sin(10*(t-delay)))
        gust.keyframe_insert(data_path="value",frame=f)
    gust.keyframe_insert(data_path="value",frame=48)

leaf_palette = [material(n,c,.56)[0] for n,c in [
    ("Russet leaf",(.38,.093,.015)),("Ochre leaf",(.67,.28,.028)),
    ("Dry green leaf",(.28,.31,.044)),("Leaf veins",(.29,.128,.024))]]
for mat in leaf_palette[:3]:
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Subsurface Weight"].default_value = .09

def leaf(name, length, color):
    verts, polys = [], []
    for i in range(17):
        t = i / 16
        profile = sin(pi*t)**.8
        width = length*(.23+.036*cos(t*8*pi))*profile
        for side in (-1,0,1):
            verts.append((width*side,length*(t-.50),
                          length*(.15*(t-.40)**2+.080*abs(side)*profile)))
        if i:
            a = (i-1)*3
            polys.extend([(a,a+1,a+4,a+3),(a+1,a+2,a+5,a+4)])
    for i in range(16):
        t = i/16
        offset = len(verts)
        for s in (t,t+1/16):
            for side in (-1,1):
                verts.append((length*.012*side,length*(s-.5),length*(.15*(s-.4)**2+.006)))
        polys.append((offset,offset+1,offset+3,offset+2))
    obj = mesh(name, verts, polys,[leaf_palette[color],leaf_palette[-1]])
    for poly in obj.data.polygons:
        poly.use_smooth = True
        poly.material_index = int(poly.index >= 32)
    sol = obj.modifiers.new("Papery edge", 'SOLIDIFY')
    sol.thickness = .00011
    return obj

bpy.context.view_layer.update()
rotation = camera.rotation_euler.to_matrix()
sensor = camera.data.sensor_width/camera.data.lens
aspect = scene.render.resolution_y / scene.render.resolution_x

def in_shot(u,v,depth):
    return camera.location + rotation @ Vector(((u-.5)*depth*sensor,
                                    (v-.5)*depth*sensor*aspect,-depth))

for i,(start,u,v,fall,depth,length) in enumerate([
        (1.02,.731,1.06,.65,.76,.031),
        (1.13,.922,1.08,.34,1.25,.046),
        (1.48,.095,1.10,.53,.69,.039),
        (1.69,.827,1.14,.32,1.08,.031),
        (1.92,.944,1.16,.42,1.5,.050),
        (2.21,.704,1.13,.29,1.28,.043),
        (2.42,.090,1.10,.42,.82,.034)]):
    obj = leaf("Tracked leaf" if i == 0 else "Falling leaf %02d"%i,length,i%3)
    for f in range(1,49):
        t = (f-1)/12-start
        x = u+.047*t+.021*sin(6*t+i)*min(1,max(0,t)*3)
        y = v-fall*t+.022*sin(7*t)
        obj.location = in_shot(x,y,depth+.034*sin(t*3+i))
        obj.rotation_euler = (-.21+.69*sin(t*6+i),.25+1.07*sin(t*5+i),
                              .43*t+.55*sin(t*4+i))
        obj.keyframe_insert(data_path="location",frame=f)
        obj.keyframe_insert(data_path="rotation_euler",frame=f)

scene["Character credit"] = "Ivo adapted from Einar Rig (CC BY 4.0), Blender Foundation | studio.blender.org"
scene["Environment credit"] = "Jolcham Oak Bark by Charlotte Baglioni, and Autumn Meadow by Sergej Majboroda (Poly Haven, CC0)"
for text, frame in [("Watching",1),("Breeze",13),("Eye lead",15),
                    ("Head follows",18),("Settling",32),("Blink",35),("Hold",42)]:
    scene.timeline_markers.new(text,frame=frame)
scene.frame_set(1)
# Pack source maps so a saved scene remains portable.
for image in bpy.data.images:
    if not image.packed_file and image.filepath.startswith(str(ASSETS)):
        image.pack()
