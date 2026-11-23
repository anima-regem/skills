# Physics engines

Select for the effect and the delivery environment. Prefer the solver already available in the project when it supports the required behavior.

| Scene need | Starting point |
| --- | --- |
| Offline 3D shot with rigid props, cloth, or fluids | Use the appropriate Blender physics system and bake its cache once the shot works. [Blender physics](https://docs.blender.org/manual/en/latest/physics/index.html) · [Baking](https://docs.blender.org/manual/en/latest/physics/baking.html) |
| Interactive 3D in Three.js | Use Rapier for solid bodies, collisions, and joints. [Three.js physics](https://threejs.org/manual/pages/physics.html) · [Rapier rigid bodies](https://rapier.rs/docs/user_guides/javascript/rigid_bodies/) |
| Interactive Godot scene | Use the project's configured engine. Check the installed version's Jolt support for 3D and use Godot's 2D physics bodies for 2D. [Godot physics](https://docs.godotengine.org/en/stable/tutorials/physics/physics_introduction.html) · [Jolt in Godot](https://docs.godotengine.org/en/stable/tutorials/physics/using_jolt_physics.html) |
| Interactive 2D outside Godot | Matter.js is a JavaScript option for the web. Box2D is a 2D rigid-body library with contact and joint constraints. Confirm the runtime and unit scale. [Matter.js](https://brm.io/matter-js/docs/) · [Box2D](https://box2d.org/documentation/) |
| Specialist effects for an offline shot | Consider Houdini Vellum for cloth, grains, and soft bodies that interact. Consider FLIP when a featured liquid shot needs breaking waves, spray, or foam. [Vellum overview](https://www.sidefx.com/docs/houdini/vellum/overview.html) · [Vellum and FLIP comparison](https://www.sidefx.com/docs/houdini/vellum/vellumvsflip.html) |
| Detailed articulated mechanics | Consider MuJoCo when joint actuators, loads, or contact dynamics are the subject of the shot. Set up the model and its controls explicitly. [MuJoCo overview](https://mujoco.readthedocs.io/en/stable/overview.html) |

Before simulating, check unit scale, collision shapes, and starting pose or velocity. Use a fixed physics timestep in interactive scenes and sample or interpolate for display. For offline delivery, bake the approved simulation and verify it plays correctly in the destination scene. [Godot fixed ticks](https://docs.godotengine.org/en/stable/tutorials/physics/interpolation/physics_interpolation_introduction.html) · [Blender baking](https://docs.blender.org/manual/en/latest/physics/baking.html)

## Reuse environmental effects

Look for an engine sample, editable project, or baked effect with suitable terms. Check its tool version, dependencies, scale, inputs, and whether the asset exposes the controls the scene needs.

- **Visual effect.** Reuse a loop or cache when playback alone covers the visible behavior. Check its speed, scale, and seams.
- **Environment drives motion.** Reuse a flow or force field or the engine's built-in force system when the environment needs to move subjects and props. Apply it where it belongs and test how participants enter and leave it.
- **Participants change the environment.** Layer a local effect over a baked base when that covers the response, such as ripples around a moving character. Reuse an editable simulation when obstacles or moving bodies need to alter the main flow. Add feedback forces when the simulated flow also needs to push the bodies. Test at low resolution before caching. [Unreal baked river workflow](https://dev.epicgames.com/community/learning/tutorials/Y5J6/unreal-engine-baked-river-simulations-overview-and-quick-start) · [Houdini fluid-object collisions](https://www.sidefx.com/docs/houdini/fluid/sopcollisions.html) · [Houdini fluid feedback](https://www.sidefx.com/docs/houdini/fluid/tips.html)

For a river, research the channel slope, depth, roughness, and obstacles. Check where current pushes, objects float or settle, and bodies make wakes. Unreal's Water plugin includes a buoyancy example and can apply river forces. SideFX links downloadable FLIP scenes in its masterclass and documents how to adapt the riverbed and colliders. Check the sample's version and terms before reuse. [USGS river velocities](https://pubs.usgs.gov/circ/2003/1246/report.pdf) · [Unreal buoyancy example](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-buoyancy-component-in-unreal-engine) · [SideFX scene files](https://www.sidefx.com/tutorials/flip-fluids-1/) · [SideFX river setup](https://www.sidefx.com/docs/houdini/fluid/splashingwater.html)
