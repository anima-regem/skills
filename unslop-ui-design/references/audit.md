# UI audit worksheet

Use this for a screen-by-screen review. Scale the depth to the request; do not make the worksheet part of the product UI.

## Task brief

Record the audience, situation, desired result, critical path, surface type, and constraints. Separate different users or journeys. Identify the evidence inspected: rendered screens, existing behavior, source, analytics, or user feedback. Distinguish observed friction from hypotheses, durable preferences from project choices, and actual criteria from comfort targets.

For an existing product, name the routes, forms, data, public component contracts, analytics hooks, accessibility behavior, and identity that must survive the redesign. Keep this review record outside the product UI.

## Element inventory

Inspect every visible element in each requested screen and relevant state. Group repeated elements only when their role and treatment are identical.

| Screen / state | Element | User benefit or problem | Decision | Change and reason |
| --- | --- | --- | --- | --- |
| Gallery / browse | “Your language. Your world.” | Repeats the context without helping selection | Remove | Give the font previews the visual emphasis |
| Gallery / font detail | License summary | Helps decide whether the intended use is allowed | Keep | Offer the full license alongside the download |
| Builder / export blocked | “3 letters need review” | Explains why export needs attention | Simplify | Link directly to the unresolved items |
| Builder / network failure | Connection message | Explains the failed request and recovery | Contextual help | Place the error and retry beside that operation |

Decisions:

- **Keep:** an action, distinction, disclosure, or expressive element has a clear role. Improve execution if needed.
- **Simplify:** retain the benefit with less repetition or a clearer control, label, grouping, or hierarchy.
- **Move:** retain infrequent detail at a discoverable point of need, or place developer setup in project docs. Name the destination and how users find it.
- **Remove:** the element contributes no defensible benefit in this context, duplicates another element, distracts from the task, or misrepresents reality.

“Looks AI-generated” is not a sufficient rationale. Identify the concrete issue: redundant content, generic treatment, misleading state, weak composition, poor legibility, or competing hierarchy.

## Practical review checklist

### Purpose and hierarchy

- [ ] The audience and primary task are explicit in the review.
- [ ] The next useful action is clear without reading a promotional paragraph.
- [ ] Navigation and instructions do not repeat the same job in multiple places.
- [ ] Secondary controls remain discoverable without competing for equal emphasis.
- [ ] Critical information and primary actions remain accessible when details are collapsed.
- [ ] Every visible element has an inventory decision and reason.

### Visual quality

- [ ] The interface has a specific, coherent direction suited to its content.
- [ ] Type scale, alignment, proportions, whitespace, and density create a readable hierarchy.
- [ ] Color, surfaces, imagery, and motion feel intentional and consistent.
- [ ] The design's expressive choices fit this surface rather than a mandatory landing-page template.
- [ ] Narrow layouts, long names, real content, zoom, and relevant writing systems hold up.
- [ ] Removing filler has not left a broken composition or erased useful identity.

### Truth and usefulness

- [ ] Metrics, samples, claims, downloads, and interactions represent real behavior or are clearly identified as mockup content.
- [ ] Status and version details appear when they affect a user decision or recovery.
- [ ] Necessary limitations, license terms, and generated-content distinctions remain accessible.
- [ ] Media and reference-inspired work have appropriate provenance and required attribution.
- [ ] Developer setup is in documentation; actionable user troubleshooting is near the failure.
- [ ] Empty, loading, error, and success states help the user proceed.
- [ ] Permission, retry, interruption, and undo or confirmation paths are covered where relevant.

### Interaction and evidence

- [ ] Labels, keyboard operation, focus, contrast, targets, and reduced motion have been checked as applicable.
- [ ] Actual foreground/background pairs and interactive states have been measured where needed.
- [ ] Frequent actions remain direct, and optional motion does not delay content or controls.
- [ ] Relevant loading and interaction costs have been measured before claiming performance gains.
- [ ] The primary path has been exercised through to a real result.
- [ ] A relevant failure or interruption has a recovery path.
- [ ] Rendered screens have been inspected at representative sizes and states.
- [ ] Findings distinguish verified behavior from recommendations and untested assumptions.

## Review output

Prioritize blocked or misleading tasks first, then decision friction, then visual polish. For each finding, include its location, observed effect, concrete remedy, and verification needed. Group repeated symptoms by their shared cause. Mark checklist items as unverified when evidence is unavailable; never treat a checked box as a substitute for evidence or report a stylistic preference as a verified defect.
