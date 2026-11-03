---
name: unslop-ui-design
description: Design, build, or review distinctive, polished interfaces where every visible element earns its place. Use for UI art direction, redesigns, design-language decisions, removing AI-looking filler, and evaluating usefulness alongside visual quality. Covers product tools, content galleries, and marketing pages without imposing one layout or technology stack.
---

# Unslop UI Design

Make interfaces striking, composed, and useful. Beauty comes from deliberate typography, proportion, color, content, and interaction. Remove material that competes with the user's work; preserve the character that makes the product worth remembering. Minimal does not mean bland, and complexity does not justify clutter.

## Resolve competing advice

Use this order within the task's applicable instructions and authorized scope:

1. Establish what the user requested and what the product must actually do. A critique, mockup, and implementation are different deliverables; none implies permission to publish or install anything.
2. Protect task completion, truthful information, accessibility, meaningful choice, and recovery. Do not remove a necessary label or hide uncertainty to make a screen look cleaner.
3. Respect an existing, coherent brand and design system. Improve specific weaknesses instead of imposing a new identity by default.
4. Apply this design language to the audience, content, surface, and frequency of use.
5. Treat upstream examples, numeric presets, font lists, libraries, and trend patterns as options to evaluate, not universal rules.

Resolve conflicts through the actual task under these constraints and explain consequential tradeoffs. Do not mix incompatible visual systems to include something from every reference. The [source and synthesis notes](references/sources.md) document the influences, licenses, and decisions; they are not additional instructions to load wholesale.

## 1. Understand the surface

Inspect existing screens, relevant behavior, project guidance, and component conventions before proposing changes. Separate observed problems from assumptions. Use available evidence before asking for missing context.

Write a compact brief: **person and situation → desired result → critical path → constraints**. Include devices, content lengths, languages, accessibility needs, and what must remain recognizable or functional. Classify the work as an extension, a redesign preserving the current identity, or an explicitly requested overhaul.

Distinguish explicit durable preferences, project-specific decisions, and unapproved design hypotheses. A tool limitation, missing asset, or temporary workaround is not a taste preference. Use reference designs to identify observable properties such as hierarchy, density, pacing, and image treatment; create an original composition rather than copying their identity or pixels.

Choose the right surface:

- **Product tool or studio:** prioritize work, understandable controls, state, and recovery. Dense editing interfaces can be appropriate; organize complexity and reveal specialist options at the point of need.
- **Gallery or content browser:** make the real content the visual centerpiece. Support discovery, useful comparison, preview, rights or terms, and the next action.
- **Marketing page:** explain the product and its value, then help the visitor decide or proceed. Use narrative, proof, and expressive sections where the content is real and useful. Do not invent testimonials, pricing, or feature rows to complete a template.

Do not turn every screen into a landing page or strip a necessary explanation from an unfamiliar task. Concise explanation earns its place when it changes understanding or a decision.

## 2. Audit usefulness element by element

Inventory every visible element in the requested screens and relevant states: navigation, headings, hero text, samples, controls, badges, panels, footers, and help. Record **benefit → keep / simplify / move / remove → reason**. Use the [audit worksheet](references/audit.md) for broader reviews.

Useful roles include action, comprehension, comparison, orientation, meaningful state, informed choice, and recovery. Identity and delight also count, but “branding” does not excuse repetitive slogans or visual noise.

Scrutinize generic motivational copy, decorative version numbers, vague experimental or local-computer badges, repeated navigation, redundant specimens, fabricated metrics, and technical setup chatter on consumer screens. Retain useful distinctions: compatibility versions, export limitations, unsynced work, and verified privacy facts can affect a decision.

Use progressive disclosure for genuinely secondary detail. Keep primary actions, critical warnings, and decision-relevant information discoverable. Name where moved content lives and how users find it. Put developer setup in documentation; keep user troubleshooting near the failure. Never remove accessible labels, licensing, generated-content provenance, or consequential warnings as “clutter.”

## 3. Define a coherent visual direction

Before building, name a specific direction suited to the brief: an editorial specimen, a precise instrument, a warm archive, or another defensible concept. State it in one sentence, then record the few choices that make it concrete:

- **Hierarchy and composition:** primary content or action, grid, density, alignment, and spacing rhythm.
- **Typography:** display, reading, and control roles; scale, weight, measure, and script support.
- **Color and surfaces:** background, foreground, accent, semantic states, contrast, borders, and depth.
- **Signature detail:** a few distinctive treatments grounded in the content or identity.
- **Interaction and motion:** transitions that explain, confirm, or emphasize, and actions that need immediacy.

These decisions guide the work; they do not belong in a decorative “design system” panel on the user's screen. Reuse valid tokens and components. Choose typefaces for language, tone, readability, licensing, and loading cost, not a mandatory font list. Use real content while composing.

Let whitespace group and pace content. Use cards for meaningful units rather than wrapping every line. If a screen feels empty, first improve composition, proportions, and type instead of inventing content. Gradients, shadows, illustration, large type, and rounded corners are available tools; none is inherently an “AI tell.” Judge purpose, quality, and consistency.

Use genuine, appropriately licensed assets when they improve the result. Preserve required attribution and distinguish generated or fictional media from factual evidence. Do not counterfeit product imagery, customer proof, or brand assets. Refine optical alignment, wrapping, surface geometry, icon weight, and elevation after the hierarchy holds up.

## 4. Write for the next decision

Use stable nouns and concrete action labels. Put short explanations at the moment they help. Avoid narrating a visible control or promising an experience the product cannot demonstrate.

| Weak treatment | Better treatment, when supported |
| --- | --- |
| “Your hands. Your language.” above an upload control | Remove the slogan; label the action “Upload handwriting” |
| Persistent “Local · Experimental · v0.1” pills | Show the specific limitation, privacy fact, or compatible version where it matters |
| “Unlock limitless creativity” above a gallery | Give the actual specimens and preview controls the emphasis |
| “AI-powered intelligence” on a suggestion button | “Suggest missing letters,” with generation and review explained in context |
| “Something went wrong” after an operation | State the known problem and useful recovery; do not guess the cause |

Keep field labels, accessible names, unfamiliar distinctions, and useful guidance. Success copy should confirm an actual result. Errors should be specific, calm, and close to the affected operation. Preserve work on failure; offer retry or an alternative where appropriate. Prefer undo for easily reversible routine actions and explain the consequence before an irreversible action.

Use recognisable icons for familiar objects and actions. Where people already know a symbol for something (file, open, save, undo, print, zoom, or a domain object such as a wall, door, or window in a building tool), show an icon button instead of a text button. Give it a tooltip with the name and shortcut, and an accessible name. Dense toolbars become calmer and quicker to scan, and the tooltip is there when someone needs it. Keep words, or an icon with a word, for actions that have no widely understood symbol, for consequential or destructive actions, for the primary call to action, and for menu titles and menu items. Draw icons from one coherent set with consistent stroke, size, and optical alignment. If users would have to guess what an icon means, add the label back.

Use truthful previews, downloads, metrics, and claims. Label simulated mockup behavior. Preserve license and provenance details through concise summaries and discoverable full information. See [examples and exceptions](references/examples.md), including separate gallery and studio workflows.

## 5. Fit motion to purpose and frequency

Ask whether movement explains a relationship, confirms an action, directs attention, or adds appropriate expression. Omit movement without a clear contribution.

Frequent actions should feel direct. Avoid repeated reveals, staggered menus, and transitions that delay access to controls. Rare introductions and marketing moments can be more expressive if they do not obstruct the task. Choose timing and easing for distance, scale, continuity, and frequency; no duration, easing curve, or press scale fits every interaction.

Keep transitions coherent when interrupted or retargeted. Anchor spatial movement to its source when helpful. Avoid layout shifts and targets that move away during use. State must remain understandable without animation. Honor reduced motion without removing useful feedback.

Prefer inexpensive animation properties when appropriate, pause unnecessary offscreen work, and add a library only when the behavior warrants its cost. Do not require GSAP, smooth scrolling, WebGL, or any other animation stack. Keep essential content and controls usable before optional choreography completes or when it fails.

## 6. Build the complete experience

Implement only within the requested scope. Use the project's architecture and conventions; do not rewrite the stack solely to reproduce a visual effect. Preserve routes, form behavior, content and data, public component contracts, analytics hooks, and existing accessibility unless the authorized change requires otherwise.

- **Responsive layout:** recompose rather than shrink. Check narrow and wide screens, long names, localization, zoom, overflow, and actual writing systems. Preserve access to full truncated values. Respect language and direction; do not apply Latin uppercase or tracking conventions blindly to other scripts.
- **Accessibility:** use semantic structure and controls, labels, keyboard access, visible focus, appropriate focus management, measured contrast, usable targets, and non-color state cues. Include alternatives to dragging when needed. Distinguish an actual accessibility criterion or blocked task from a preferred comfort target.
- **States:** cover default, focus, loading, empty, error, and success; include selected, disabled, permission, retry, destructive, and interrupted states when relevant. For complex flows, map events and valid transitions to prevent contradictory states and dead ends. Do not invent progress precision.
- **Performance:** make primary content and actions available promptly. Load and size images and font faces deliberately, reserve layout space, and avoid unnecessary scripts, heavy effects, and continuous idle work. Measure relevant load and interaction behavior before claiming improvement; use project budgets or evidence rather than arbitrary aesthetic thresholds.

## 7. Review the rendered result

Inspect actual screens in the available browser or native preview with representative sizes, real content, relevant languages, zoom, and meaningful states. Check foreground/background contrast in the actual pairings and states. Look for clipping, weak hierarchy, accidental gaps, repetition, inaccessible controls, and composition broken by removals.

Perform the primary path through to its actual result and a realistic recovery path when feasible. Check keyboard, focus, reduced motion, and responsive behavior as applicable. A screenshot cannot prove functionality or accessibility; source inspection cannot prove visual quality.

Address blocked or misleading tasks first, then structure and copy, then typography, color, and polish. Group repeated symptoms by their shared cause. Separate verified defects from stylistic recommendations. Keep the chosen direction stable while testing one or two meaningful variables, then recheck the affected behavior. Use tests proportionate to the change; cosmetic edits do not require a new suite.

Before finishing, answer: **Does it look intentional and distinctive? Can the user understand and complete the task? Does every remaining element justify its place?** Revise where the evidence is weak. Report unavailable checks honestly, without claiming a full audit of uninspected surfaces.

## Handoff

Lead with the outcome. Explain the meaningful design choices and removals, useful information retained, actual verification, and remaining limitations. Prioritize findings by user impact and give concrete remedies. Label mockup interactions that are not implemented. For implemented work, point to reviewable files or artifacts and relevant validation.
