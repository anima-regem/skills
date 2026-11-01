---
name: unslop-ui-design
description: Design or audit distinctive, polished product UI while removing filler and clutter that do not help users. Use for requests to unslop AI-looking interfaces, assess whether screen elements are useful, or redesign a beautiful but gimmicky or overloaded UI. Supports critique, mockups, and implementation within the requested scope.
---

# Unslop UI Design

Create a beautiful interface whose content, controls, and visual hierarchy serve the people using it. Make beauty through typography, proportions, composition, color, material, and interaction quality. Removing filler should sharpen the product's character, not erase it.

## 1. Establish the job

Before changing a screen, identify:

- **Person and situation:** who is here, what they know, and whether they are exploring, creating, comparing, or recovering from a problem.
- **Desired result:** the concrete outcome they came for.
- **Critical path:** the shortest understandable sequence to reach that result, including necessary decisions and recovery.
- **Constraints:** existing design system, brand, content, device sizes, language, accessibility needs, and product behavior.

Use available product evidence first. State assumptions briefly; ask only when missing context would materially change the design. Separate different audiences and tasks instead of giving every screen the same hero, instructions, or controls.

Match the deliverable to the request. For an audit, inspect and recommend. For a mockup, show the proposed experience and identify simulated behavior. Change application code only when implementation is requested. This skill does not authorize installation, publishing, or unrelated product changes.

## 2. Make every visible element earn its place

Inventory the requested screens, including headers, footers, cards, badges, sample text, tooltips, and persistent status. For each element, name its user benefit and choose **keep**, **simplify**, **move to contextual help or documentation**, or **remove**, with a specific reason. Use the [audit worksheet](references/audit.md) when the review spans multiple screens.

Useful roles include taking an action, understanding content, comparing options, knowing location or meaningful state, making an informed decision, and recovering from failure. Brand identity and expressive composition can also provide orientation, recognition, and delight; decorative elements need proportion and intent, not invented functional excuses.

Scrutinize these common sources of filler:

- Generic slogans that repeat the product name or obvious task, such as “Your hands. Your language.”
- Gratuitous version numbers, “experimental” pills, “local” badges, and implementation labels.
- Duplicate navigation, repeated hero specimens, redundant instructions, and containers that only repeat headings.
- Fabricated metrics, testimonials, social proof, live activity, or functionality.
- Install commands, dependencies, build output, and repository setup on ordinary consumer screens.

Judge the actual decision, not a blacklist. A compatibility version, actionable offline state, or limitation that affects output can be essential. Keep truthful warnings and uncertainty where they affect consent, trust, quality, or recovery. Move developer setup to project documentation; keep actionable user troubleshooting near the problem.

## 3. Build a coherent visual direction

Choose a specific direction suited to the product and audience: for example, an editorial type specimen, a quiet precision tool, or a vivid creative workspace. Explain the direction in one sentence, then make it visible in the design.

- **Typography:** establish a deliberate display/body/control hierarchy. Use readable measures, intentional weights, and spacing suited to the script. Do not apply Latin uppercase or tracking conventions blindly to other writing systems.
- **Composition:** make the primary task easy to locate through scale, placement, alignment, and contrast. Use whitespace to group and pace content. Let real content determine the grid and density.
- **Palette and surfaces:** give color semantic roles and a coherent mood. Borders, shadows, gradients, and rounded corners should establish depth, grouping, or character consistently.
- **Expressive detail:** use illustration, large type, imagery, or motion where it improves understanding, identity, or enjoyment without delaying the main action. Avoid filling empty space merely because it is available.
- **Responsive behavior:** recompose for narrow screens and long or translated content; do not simply shrink the desktop layout. Keep the next useful action reachable.

Respect a valid existing design system. Extend it deliberately where necessary instead of replacing it with a generic template. No color, gradient, font, radius, or layout is inherently an “AI tell”; assess its execution and fitness for this product.

## 4. Write useful interface copy

Name actions by their result: “Upload handwriting,” “Review suggestions,” “Download font.” Use familiar, concrete language. Put instructions at the moment they help, and remove prose that merely narrates a visible control.

Keep labels and necessary distinctions. An icon-only button still needs an accessible name; a placeholder does not replace a field label. Explain unfamiliar or consequential choices briefly. Errors should say what happened and what the user can do next. Success should confirm the result and offer a useful next action when one exists.

Use real content and truthful product capability. Do not imply that a font is complete, a generated suggestion is accurate, an upload is private, or a download is available unless verified. Preserve substantive license and generated-content provenance information; use concise summaries with accessible details rather than hiding consequential terms.

Read [examples and exceptions](references/examples.md) for before/after microcopy and the separate font-creation and font-gallery use cases. Adapt the reasoning, not the literal layout or copy.

## 5. Finish the interaction, not just the screenshot

For each relevant task, design the default, focus, loading, empty, error, and success states. Add disabled, selected, destructive, and interrupted states where the behavior needs them.

- Preserve keyboard operation, visible focus, semantic controls, accessible names, readable contrast, and comfortable targets.
- Make status understandable without color alone. Announce important asynchronous results to assistive technology when appropriate.
- Keep input and work recoverable when an operation fails. Show progress when waiting is meaningful; do not invent precision or completion estimates.
- Give motion a purpose, such as explaining a transition or confirming an action. Honor reduced-motion preferences and avoid blocking task completion with animation.
- Keep useful help discoverable. Moving content off the main screen must not make a necessary decision or recovery path hard to find.

## 6. Implement and verify within scope

When implementing, use the project's existing components and conventions where they fit. Preserve working behavior, data, and meaningful states while improving the interface. Do not add a dependency or rewrite architecture solely to achieve a visual effect.

Inspect actual rendered screens using the available browser or native preview. Check representative wide and narrow sizes, long content, relevant languages, zoom, and the states exercised by the critical path. Check for clipped text, weak hierarchy, awkward gaps, duplicated content, hidden actions, and visual regressions. A source-code review alone cannot verify visual quality.

Perform the real primary interaction, including its result and a realistic failure path when feasible. Use tests appropriate to changed behavior; a cosmetic edit does not require a new test suite. Recheck after material fixes. If rendering, interaction, or assistive-technology checks are unavailable, state exactly what remains unverified.

Before finishing, ask: **Is it distinctive and beautiful? Can the user understand and complete the task? Does every remaining element justify its place?** Revise when any answer is weak.

## Handoff

Lead with the outcome. Summarize the meaningful removals and redesign choices, the retained information that affects user decisions, what was actually verified, and any unresolved limitation. For an audit, prioritize findings by task impact and give concrete remedies. For a mockup, label unimplemented interactions. For an implementation, point to the changed files or reviewable artifact. Avoid presenting an untested aesthetic opinion as proof of usability.
