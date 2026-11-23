---
name: lazy-architect
description: Find and adapt the closest working foundation when building a feature, tool, workflow, skill, or design artifact. Use automatically when an existing implementation, template, native capability, or open-source project could save substantial work, including when choosing what to build on.
---

# The Lazy Architect

Start as close to the finished job as you can. Spend the custom work on the part that makes this request different.

**Define “close” with an acceptance example.** Identify what goes in, what someone must be able to do with the result, and which constraints could rule out an otherwise good match. Keep the user's chosen stack, format, and scope.

**Look for something that already does the hard part.** Inspect the project's working features, installed tools, and platform capabilities. When there is a meaningful gap, search the public web for the actual operation and its hardest constraint. Try the upstream examples, maintained implementations, or reusable templates in the relevant ecosystem. Open the candidate itself. For code, find the API, implementation, or example that performs the operation. For other artifacts, inspect an actual specimen and its editable source. Respect local-only requests and keep private project details out of public queries.

**Choose by the work left over.** For plausible candidates, identify what works as supplied, what you need to change, and what you would inherit. Weigh integration effort, ongoing ownership, and terms for the material you intend to reuse. Check upstream maintenance and compatibility when taking on a dependency. A close functional match can still be expensive if it needs a fork or a second runtime. Try the hardest requirement on a small example before a costly commitment. A sound local solution can settle the choice immediately. Stop searching when another lead is unlikely to change the decision.

**Use the foundation.** In an implementation task, connect or adapt the chosen piece through its supported interface and finish the missing behavior. In a research or design task, deliver the requested recommendation or artifact. Where a candidate only illustrates an idea, use that idea as a reference and create your own expression. If available foundations cost more to adapt than a small custom piece, build that piece and keep the rest.

**Prove the fit.** Exercise the acceptance example at the real entry point, including the constraint most likely to break the choice. For a consequential external dependency or artifact, identify the source and version used, the custom part, and any unverified assumption that changes the decision.

For examples of narrowing the search, trying a foundation, or justifying a custom part, see [reuse decisions](references/reuse-decisions.md).
