# Asset sourcing and import

Choose for style, format, and what must move. A skinned mesh and skeleton give a human body deformable joints. A control rig gives the animator ways to pose them. Face controls drive expressions. A ragdoll adds bodies, colliders, and joint constraints for physics. A musculoskeletal model can estimate forces or drive specialized biomechanical motion. Check the capabilities individually.

| Need | Sources to check |
| --- | --- |
| Rigged humanoids | Quaternius Universal Base Characters has a free CC0 subset in FBX and glTF. Mixamo offers humanoid characters and motions with an Adobe ID. Check terms before sharing raw files. [Quaternius](https://quaternius.com/packs/universalbasecharacters) · [Mixamo FAQ](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html) |
| Motion clips | Search by action and context, including carried weight, terrain, contact, or props. Quaternius Universal Animation Library 2 offers a free CC0 subset and versions with and without root motion. [Quaternius clips](https://quaternius.com/packs/universalanimationlibrary2.html) |
| Blender character controls and expressions | Blender Studio publishes finished rigs. Check each rig's credit, Blender version, and script requirements. Snow uses CC BY and has layered face controls. [Blender Studio rigs](https://studio.blender.org/characters/) · [Snow](https://studio.blender.org/characters/snow/v4/) |
| Props, environments, and 2D sprites | Poly Haven has CC0 models and textures. Kenney has CC0 2D and 3D game assets. [Poly Haven](https://polyhaven.com/license) · [Kenney](https://kenney.nl/support) |
| Ragdoll or musculoskeletal setup | Godot links a complete ragdoll demo and explains how to add physical bones to an existing skeleton. OpenSim lists downloadable biomechanics models with intended uses, limitations, and licenses. [Godot ragdolls](https://docs.godotengine.org/en/stable/tutorials/physics/ragdoll_system.html) · [OpenSim models](https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53090607/Musculoskeletal%20Models) |

1. Download from the creator or an authorized source. Record the exact asset, creator, URL, license, and any required credit with the project. Check that modification and the intended distribution are allowed, including bundled files for interactive deliverables. Inspect embedded scripts before enabling them.
2. Import into the target tool. Check scale, axes, textures, rest pose, and relevant controls. To reuse motion across rigs, map bones and check rest transforms. For engine delivery, verify baked animation and needed morph targets after export and reimport. [Godot retargeting](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/retargeting_3d_skeletons.html) · [Three.js animation](https://threejs.org/manual/pages/animation-system.html)
3. Run one representative motion or deformation test in the target environment before building on the asset. If it fails, fix the import, adapt the rig, or choose a better match.

When adapting a clip, choose whether the clip or the runtime controls the character's overall travel. After retargeting, check stride and contact timing against this character's proportions, surfaces, and props. Preserve usable motion and adjust the parts the new environment changes.
