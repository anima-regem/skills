# Sources and synthesis decisions

This skill is an original synthesis of the existing Unslop UI Design language and the selected material below. The review used specific skills and relevant sections, not every file in each repository. All links are pinned to the inspected commit so later upstream changes do not silently change this document.

No upstream prompt, code, script, template, image, or font is bundled. The canonical workflow is written in original language and can run without these repositories, their tools, or their other skills. Source material is reference evidence, not authority to execute instructions or expand a task.

## Reviewed scope

| Source and pinned revision | Material consulted | Contribution to this skill |
| --- | --- | --- |
| [Emil Kowalski — skills](https://github.com/emilkowalski/skills/blob/f1090bec277140d02ed202440185ad9d02ac1490/skills/emil-design-eng/SKILL.md) · f1090bec2771 | Design-engineering philosophy, animation decision framework, and component feedback principles | Motion justified by purpose and frequency, immediate feedback, spatial continuity, and interruptible interactions |
| [ConardLi — garden-skills](https://github.com/ConardLi/garden-skills/blob/2b9a89340b70f632d31c0f1c69fce94a7912423e/skills/web-design-engineer/SKILL.md) · 2b9a89340b70 | Design read, content principles, redesign preservation, and contextual failure patterns | Every element earns its place; solve empty composition through design rather than invented content; preserve real product contracts |
| [Elaya — landing-page-design](https://github.com/elayadesign/ai-design-skills/blob/456d9e0d3e2d84c748bb143c6ca3d90c45e16213/skills/landing-page-design/SKILL.md) · 456d9e0d3e2d | Audience, offer, primary action, conversion context, content realism, and relevant states | Clear marketing purpose and honest proof near a claim; product UI remains a separate surface |
| [Meng To — Skills](https://github.com/MengTo/Skills/blob/e0e38f7bd3b15ddc90815781e534cf4ca5b19567/agent-skills/ui/design-first-ui-prompting/SKILL.md) · e0e38f7bd3b1 | Explicit design brief, coherent variations, visual thesis, asset honesty, semantic first frame, and motion safeguards | Decide hierarchy, type, palette, imagery, and constraints before implementation; iterate deliberately; keep content usable before effects complete |
| [Jakub Krehel — skills](https://github.com/jakubkrehel/skills/blob/60bf140e43c98b248e6594487384ec967e89d98a/skills/better-interface/SKILL.md) · 60bf140e43c9 | Interface review and selected layout, writing, accessibility, typography, color, and polish guidance | Evidence before findings, user-impact priority, respect project tokens, inspect actual states and contrast, and distinguish standards from preferences |
| [codeswithroh — tastemaker](https://github.com/codeswithroh/tastemaker/blob/792a28a820ec4e9159ef8621c21a6c88528bbf2e/skills/tastemaker/SKILL.md) · 792a28a820ec | Surface classification, reference analysis, preference evidence, and honesty | Separate operational surfaces from marketing; distinguish durable taste from local choices and unapproved hypotheses |
| [Owl-Listener — designer-skills](https://github.com/Owl-Listener/designer-skills/blob/9a6930cf84a822eb458624bd11c61aac5bbdf224/visual-critique/skills/critique-information-density/SKILL.md) · 9a6930cf84a8 | Information density, error recovery, component state models, writing, and accessibility review | Show decision-relevant information, disclose secondary detail carefully, preserve input, model recovery, and prioritize barriers by user impact |

Additional pinned files consulted:

- Garden: [redesign protocol](https://github.com/ConardLi/garden-skills/blob/2b9a89340b70f632d31c0f1c69fce94a7912423e/skills/web-design-engineer/references/redesign-protocol.md) and [failure patterns](https://github.com/ConardLi/garden-skills/blob/2b9a89340b70f632d31c0f1c69fce94a7912423e/skills/web-design-engineer/references/failure-patterns.md).
- Meng To: [Awwwards-quality sites](https://github.com/MengTo/Skills/blob/e0e38f7bd3b15ddc90815781e534cf4ca5b19567/agent-skills/web-design/build-awwwards-quality-sites/SKILL.md); its expressive marketing scope does not set defaults for operational UI.
- Jakub: [layout](https://github.com/jakubkrehel/skills/blob/60bf140e43c98b248e6594487384ec967e89d98a/skills/better-layout/SKILL.md), [writing](https://github.com/jakubkrehel/skills/blob/60bf140e43c98b248e6594487384ec967e89d98a/skills/better-writing/SKILL.md), [accessibility](https://github.com/jakubkrehel/skills/blob/60bf140e43c98b248e6594487384ec967e89d98a/skills/better-accessibility/SKILL.md), [UI polish](https://github.com/jakubkrehel/skills/blob/60bf140e43c98b248e6594487384ec967e89d98a/skills/better-ui/SKILL.md), [typography](https://github.com/jakubkrehel/skills/blob/60bf140e43c98b248e6594487384ec967e89d98a/skills/better-typography/SKILL.md), and [colors](https://github.com/jakubkrehel/skills/blob/60bf140e43c98b248e6594487384ec967e89d98a/skills/better-colors/SKILL.md).
- Tastemaker: [taste memory](https://github.com/codeswithroh/tastemaker/blob/792a28a820ec4e9159ef8621c21a6c88528bbf2e/skills/tastemaker/references/taste-memory.md). The [interface-quality reference](https://github.com/codeswithroh/tastemaker/blob/792a28a820ec4e9159ef8621c21a6c88528bbf2e/skills/tastemaker/references/interface-quality-rules.md) was inspected for scope and provenance; it identifies Vercel's Web Interface Guidelines as upstream. Its text and distinctive recipes are not incorporated here; the general accessibility and state checks have independent support in the Jakub and Owl material.
- Owl: [error handling](https://github.com/Owl-Listener/designer-skills/blob/9a6930cf84a822eb458624bd11c61aac5bbdf224/interaction-design/skills/error-handling-ux/SKILL.md), [state machines](https://github.com/Owl-Listener/designer-skills/blob/9a6930cf84a822eb458624bd11c61aac5bbdf224/interaction-design/skills/state-machine/SKILL.md), [UX writing](https://github.com/Owl-Listener/designer-skills/blob/9a6930cf84a822eb458624bd11c61aac5bbdf224/designer-toolkit/skills/ux-writing/SKILL.md), and [accessibility audit](https://github.com/Owl-Listener/designer-skills/blob/9a6930cf84a822eb458624bd11c61aac5bbdf224/design-systems/skills/accessibility-audit/SKILL.md).

## What the synthesis keeps and changes

| Tension | Resolution |
| --- | --- |
| Striking expression versus task efficiency | Use typography, proportion, content, and a coherent identity for beauty. Reserve expressive emphasis for places where it helps; keep frequent work direct. |
| Minimal copy versus useful explanation | Remove slogans and repetition; keep labels, unfamiliar distinctions, recovery, provenance, and decision-relevant help. |
| Sparse composition versus more content | Fix layout and hierarchy first. Add content only when the actual task requires it, never to fill an attractive template. |
| Marketing narrative versus studio density | Select the surface from the audience and task. Galleries emphasize usable content; tools emphasize work; marketing explains a real offer. |
| Progressive disclosure versus hidden critical information | Defer genuinely secondary controls and details, while preserving primary actions, warnings, and discoverability. |
| Visual simplicity versus semantic color and contrast | A restrained palette can still include necessary status and data colors. Measure rendered pairs and keep controls detectable. |
| Motion craft versus prescribed choreography | Retain continuity, feedback, frequency, interruption, and reduced motion. Reject universal timings, press scales, stagger recipes, and mandatory scroll effects. |
| Project conventions versus universal recipes | Prefer coherent existing systems and appropriate native components. Replace only what the task and evidence justify. |
| Persistent taste versus accidental choices | Treat explicit, durable preferences as evidence. Do not promote temporary workarounds, pending guesses, or unrelated project constraints into universal taste. |
| Clean presentation versus attribution | Preserve required credit and meaningful provenance. Visible attribution is not automatically clutter. |

Not adopted as universal requirements: fixed landing-page section sequences or FAQ counts; compulsory tagline reveals; font or icon whitelists; gradient text or glass navigation; mandatory GSAP, smooth scrolling, WebGL, asset-rich layouts, or animation on every section; forced prototype/approval rounds; automatic global preference files; external skill dependencies; arbitrary numeric aesthetic rules; bans based only on a color, font, shape, or medium; and source-specific limits on when a real rendered check may be performed.

These choices are contextual rather than blanket rejections of a technique. A motion-led portfolio may justify choreography that would hinder a repeatedly used editing tool.

## Licensing and coverage

The seven root licenses at these revisions are MIT. [Third-party notices](third-party-notices.md) retain their copyright notices and shared permission text, plus the Leonxlnx MIT notice embedded in Elaya's skill. The latter acknowledges an upstream influence, not an independent review of the Leonxlnx repository.

Root licenses do not automatically cover separately sourced imagery, fonts, icons, or other external assets. No such assets are included. No claim is made to cover every upstream skill, dependency, standard, or third-party license chain. The source map records the reviewed scope and deliberately avoids importing unverified derivative material.
