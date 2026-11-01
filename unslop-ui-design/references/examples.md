# Examples and exceptions

These are decision examples, not mandatory phrases or universal layouts. Use only capabilities and states the product actually supports.

## Microcopy: remove filler, preserve meaning

| Before | After / treatment | Why |
| --- | --- | --- |
| “Your hands. Your Malayalam.” above an upload control | Remove the slogan; label the action “Upload handwriting” | The control explains the next step. Real handwriting samples can provide the visual character. |
| “Experience the future of creative expression” | Remove | It gives no task-specific information. Let the work and composition communicate quality. |
| “Local · Experimental · v0.1” on every screen | Remove persistent badges unless one changes a decision | Replace only meaningful limitations with precise, contextual information. |
| “No results found” | “No fonts match ‘[query]’.” plus “Clear search” | Explain the current result and provide recovery. |
| “Something went wrong” after upload | If confirmed: “The image could not be read. Choose a PNG or JPEG and try again.” | Give the actual cause and supported recovery. Do not guess the cause. |
| “AI-powered glyph intelligence” | “Suggest missing letters” | Name the useful action. Explain generation and review where the suggestions appear. |
| “Export successful!” | “Font exported.” plus the actual file or download action | Confirm an observable result. Do not promise a file that was not created. |
| An install command under a consumer download button | Move setup instructions to the contributor guide | Consumers need a usable font; developers need a separate setup path. |

## Two products, two critical paths

### Font builder

**Person:** someone creating a coherent, editable Malayalam design font from handwriting.

**Critical path:** upload ink → inspect and adjust tracing → review missing letters → preview and edit → export.

Make the artwork, glyph editing, and live font preview the visual center. Keep controls close to the glyph or operation they affect. Show completeness or review status when it changes the next action. Do not claim exact handwriting imitation: consistency, readability, and editable design are the relevant goals.

When machine-generated missing-letter suggestions are supported:

- Distinguish traced source glyphs from generated suggestions in the review context.
- Let the user compare, edit, accept, or reject suggestions before using them.
- Say “Suggested letter — review before export” where accurate; avoid unsupported confidence percentages or claims of authenticity.
- Preserve source notices, applicable licensing, and provenance through the relevant review and export paths. Compress presentation without deleting consequential information.

Useful state copy might be “12 letters need review” with a link to those letters, if that count and review requirement are real. A decorative “AI ready” badge conveys less.

### Public font gallery

**Person:** someone choosing a Malayalam font for a design, or a contributor submitting a font.

**Critical path for a visitor:** browse or search → try text → compare relevant details → check license → download.

Let live specimens show the fonts. A strong typographic composition can be both the expressive centerpiece and a functional preview. Provide readable names, meaningful controls, download format where needed, and license details. Inspect shaping, fallback, and the compiled font used by the preview; a screenshot specimen alone cannot demonstrate typed-text behavior.

Keep a clear contribution entry point for contributors. Put repository setup, build commands, dependency lists, and submission mechanics in the linked contributor documentation. Do not put builder upload/edit controls into a gallery unless that is an actual supported task.

## When apparently technical details are useful

| Detail | Keep when… | Treatment |
| --- | --- | --- |
| Version | Users must select a compatible release or distinguish changed font files | Put it beside the relevant download or release details, not in a decorative global pill |
| Offline state | A requested operation cannot run, or unsynced work needs attention | Explain the affected operation and recovery near that task; persist only while useful |
| Local processing | Verified processing behavior affects a person's privacy decision | Give a precise statement near upload or in an accessible privacy explanation; do not imply a broader guarantee |
| Experimental limitation | A known limitation changes expected output or the choice to proceed | Describe the concrete limitation and what to review; a vague “experimental” badge is insufficient |
| Generated provenance | Users need to distinguish input, suggestions, and accepted output | Show it in the relevant review/export context and preserve required notices |
| License | Usage, modification, or redistribution rights affect the design decision | Offer a concise truthful summary and the full terms at selection/download |

Removing clutter must never turn uncertain capability into false certainty. If the behavior is not known, verify it or report the uncertainty in the design handoff.
