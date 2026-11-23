# Shared optional inputs

## Face rig

`einar.blend` is a packed head-and-shoulders version of Blender Studio's production rig. It retains the modeled face, skin maps, eyes, beard, brows, clothing, and original facial controls. The character faces approximately −Y with an eye line near Z = 1.68 m in the original coordinates. The standing-height head and shoulders can be staged at sitting height by moving their common roots together.

```python
with bpy.data.libraries.load(str(assets / "einar.blend"), link=False) as (_, target):
    target.collections = ["CH-einar"]
bpy.context.scene.collection.children.link(target.collections[0])
rig = bpy.data.objects["RIG-einar"]
```

Use native pose bones and keyframe in local coordinates. `FK-Head` turns the head. `MSTR-TGT-Eyes` controls shared gaze. `Blink.L` and `Blink.R` use millimeter-scale local Y translation, with tested range −0.006 to +0.003 m. `ACT-Eyebrow_Inner.L/R` and `ACT-Eyebrow_Outer.L/R` use local Y around ±0.01 m. `ACT-Mouth_Corner.L/R` allows small local X or Y moves. `MSTR-Jaw` rotates locally. Check visible signs and ranges with the camera before committing to keys. The library can be appended with auto-execution disabled.

**Einar Rig (CC BY 4.0) Blender Foundation | studio.blender.org.** The benchmark copy trims out-of-frame geometry, packs and reduces shader maps, and uses direct groom attachments. [Publisher release and license](https://studio.blender.org/characters/einar/v1/) · [Production face and displacement notes](https://studio.blender.org/blog/layered-sculpting-for-einar/) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Environment

See [the environment asset list](environment/README.md) for the optional oak bark maps, grass tufts, and autumn meadow HDRI.
