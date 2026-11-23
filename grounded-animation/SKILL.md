---
name: grounded-animation
description: Use when creating or reviewing 2D or 3D animation where timing, acting, physical contact, weight, collisions, or material behavior matter.
---

# Grounded animation

## Establish the scene

Before authoring motion, identify the intended action, output format, and what must visibly change. For physical action, establish scene scale and time, the starting state, what supports each object, key contacts and releases, and the forces or material properties that affect the motion. Look up relevant footage or measurements when behavior is uncertain. Mark estimates and deliberate stylization.

For environmental effects, identify what causes the effect, where and when it acts, what responds, and what changes the environment in return. Use real references for the interactions that matter to the result. Check boundaries such as banks, shelter, or a waterline when they change the response.

## Reuse existing assets

Check the project first, then search for models, rigs, props, environments, motion clips, and editable simulation setups that fit the task. Verify usage terms, then download, import, and adapt suitable material before building from scratch. For people, start with a skinned humanoid with the required body and face controls. Add a ragdoll or muscle model when the behavior calls for it. See [asset sourcing and import](references/asset-sourcing.md) for models and clips, and [physics engines](references/physics-engines.md) for reusable effects.

## Choose how motion is driven

- **Animate** deliberate performance, staging, and beats that must land on cue. Block the main poses and timing first. For characters, check silhouette, joint deformation, gaze, and any needed face controls. Label primitive stand-ins as blocking.
- **Constrain** relationships that need to hold for part of the motion, such as a planted foot, a hand on a handle, or an object resting on a moving support. Check the relationship relative to the contact surface.
- **Simulate** motion that depends on forces, collisions, or materials interacting. Start with the project's existing tools. See [physics engines](references/physics-engines.md) when a solver is needed.
- **Combine** these methods by giving each moving part a primary driver at each beat. At a release into simulation, match the outgoing pose and linear and angular velocity so the body continues naturally.

## Review the motion

Make a cheap preview at the intended speed in the target view or runtime. Scrub transitions and test both sides of any relevant effect boundary. Check that contacts hold, objects react to the right causes, and motion conveys the intended weight and timing. Fix visible defects and state what remains unverified.
