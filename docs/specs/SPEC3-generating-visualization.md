# SPEC3: HTML Visualization Generation

## Overview

This spec defines the rules and behavior for Phase 2 of the LLM pipeline — generating the self-contained HTML visualization from a finalized text specification. Phase 1 (clarification/spec creation) is out of scope for this document.

---

## 1. Context Window Size

The HTML generation call must use a large context window to allow the LLM to produce highly detailed, complete visualizations without truncation.

- **`max_tokens` for HTML generation: 80,000**
- This applies to the `generate_html_from_spec` method (Phase 2 only).
- The clarification phase (Phase 1) retains its current `max_tokens` of 16,000.
- Rationale: HTML visualizations with inline CSS, JavaScript, data, and interactivity can easily exceed 20–40k tokens. An 80k ceiling gives the model room to be thorough without self-truncating.

---

## 2. Prompt: Maximize Detail and Richness

The HTML generation system prompt must explicitly instruct the LLM to produce the most detailed, visually rich, and complete visualization possible. The model should aim to use the full output capacity rather than producing a minimal implementation.

### System Prompt Requirements

The `HTML_GENERATION_SYSTEM_PROMPT` must include the following directives:

1. **Maximize detail** — The LLM should generate the most thorough, polished implementation it can. Every aspect of the spec should be fully realized, not abbreviated.
2. **Use the full output budget** — Rather than producing a minimal working version, the model should invest tokens in:
   - Rich, polished CSS styling (gradients, shadows, transitions, hover effects)
   - Comprehensive interactivity (tooltips, click handlers, animations)
   - Thorough data rendering (all data points, labels, legends, annotations)
   - Responsive layout handling
   - Accessibility attributes (aria-labels, semantic elements)
   - Inline comments explaining major sections
3. **No shortcuts** — Do not use placeholder data or "..." ellipsis markers. Every element described in the spec must be present in the output.

---

## 3. Creative Use of Visualization Libraries

The LLM must actively choose the most visually expressive tool for each visualization rather than defaulting to plain HTML/CSS. Rich, interactive, and animated library-based visualizations are always preferred over static markup when the data or content supports it.

### 3.1 Library Selection Guidance

The LLM should reason about which library or combination of libraries best serves the visualization goal:

| Library | Best for |
|---------|----------|
| **D3.js** | Custom charts, network graphs, hierarchical layouts, force simulations, geographic maps, SVG animations, any visualization that benefits from fine-grained control |
| **Chart.js** | Clean standard charts (bar, line, pie, radar, doughnut) with minimal setup; good for dashboards |
| **Plotly.js** | Scientific charts, 3D plots, statistical distributions, financial charts |
| **Mermaid.js** | Flow diagrams, sequence diagrams, Gantt charts, ER diagrams, state machines, org charts, Git graphs |
| **Plain SVG + CSS** | Infographics, process diagrams, icon-heavy layouts, custom decorative elements |
| **CSS animations + transitions** | Timeline animations, reveal effects, progress indicators, entrance/exit transitions |

### 3.2 Directive: Be Creative and Ambitious

- **Default to the richest option.** If a concept can be expressed as a force-directed graph with D3, do that — not a plain list.
- **Layer libraries.** A visualization may use D3 for the main chart and Mermaid for a workflow sidebar.
- **Use animations purposefully.** Entrance animations, transitions between states, and hover micro-interactions significantly increase the perceived quality and engagement of a visualization.
- **Avoid plain HTML tables and bullet lists** for any data that could be a chart, diagram, or visual layout. Only use tables/lists when tabular or sequential structure is genuinely the clearest format.
- **Use CDN URLs for all libraries.** They must be from official, stable CDN sources (cdnjs, jsdelivr, unpkg).

### 3.3 Impact on Prompts

`HTML_GENERATION_SYSTEM_PROMPT` and `HTML_INCREMENTAL_EDIT_SYSTEM_PROMPT` must both include an explicit "Creative Library Use" directive reinforcing the above guidance.

---

## 4. Incremental Editing Strategy

When a user edits an existing visualization (i.e., the visualization already has `current_draft_html`), the generation process must follow an **incremental update** strategy rather than regenerating from scratch. This preserves visual consistency, styling decisions, and any polish the previous generation established.

### 4.1 Two Generation Modes

The `generate_html_from_spec` method must support two distinct modes:

#### Mode A: Fresh Generation (no existing HTML)
- Used when `current_draft_html` is `None` or empty.
- The LLM receives only the spec and produces a complete HTML document from scratch.
- Prompt: "Generate a complete HTML visualization from this specification."

#### Mode B: Incremental Edit (existing HTML present)
- Used when `current_draft_html` contains a previous visualization.
- The LLM receives:
  1. The **full previous HTML** document
  2. A **description of what changed** in the spec (the delta)
- Prompt instructs the LLM to:
  - Keep as much of the existing HTML unchanged as possible
  - Only modify the sections affected by the spec changes
  - Preserve all existing styling, layout, color choices, and structure
  - Output the complete updated HTML document (not a diff/patch)

### 4.2 Spec Delta Computation

To provide the LLM with a meaningful description of what changed, the system must compare the previous spec with the new spec:

- **Previous spec**: Stored on the visualization document as the spec that was used to generate the current `current_draft_html`. Retrieved from the most recent `spec_output` message in the chat session, or from the visualization's `current_draft_spec` field.
- **New spec**: The spec just produced by Phase 1.
- **Delta prompt**: The system constructs a prompt that includes both the full previous HTML and a clear description: "The user has updated the specification. Here is the previous HTML and the updated spec. Modify the HTML to reflect the spec changes while keeping everything else identical."

### 4.3 Incremental Edit Prompt Structure

When in Mode B, the user message sent to the LLM for HTML generation should be structured as:

```
The user has updated the visualization specification. Your job is to update the existing HTML
to reflect ONLY the changes in the new specification. Keep all other HTML, CSS, JavaScript,
styling, layout, colors, and structure exactly the same.

=== EXISTING HTML DOCUMENT ===
[full previous HTML here]

=== PREVIOUS SPECIFICATION ===
[previous spec text]

=== UPDATED SPECIFICATION ===
[new spec text]

Apply ONLY the differences between the previous and updated specifications to the existing
HTML document. Output the complete updated HTML document.
```

### 4.4 Data Flow

```
Chat Router receives spec_ready from Phase 1
  │
  ├─ Fetch current visualization from DB
  │   ├─ current_draft_html exists?
  │   │   ├─ YES → Mode B (incremental edit)
  │   │   │   ├─ Retrieve previous spec (current_draft_spec)
  │   │   │   ├─ Pass existing_html + previous_spec + new_spec to generate_html_from_spec
  │   │   │   └─ LLM edits existing HTML
  │   │   │
  │   │   └─ NO → Mode A (fresh generation)
  │   │       ├─ Pass only new_spec to generate_html_from_spec
  │   │       └─ LLM generates from scratch
  │   │
  └─ Store resulting HTML as current_draft_html
      Store new spec as current_draft_spec
```

### 4.5 Why Not Diff/Patch?

Sending the LLM a programmatic diff (unified diff format) was considered and rejected because:
- LLMs are better at understanding natural language descriptions of changes than parsing diff syntax
- The spec is already a natural-language document; providing both versions lets the LLM reason about the semantic differences
- The output must be a complete HTML document regardless, so a patch-based approach adds complexity without benefit

---

## 5. Method Signature Update

`generate_html_from_spec` must be updated to accept optional parameters:

```python
async def generate_html_from_spec(
    self,
    spec_text: str,
    websocket: WebSocket,
    existing_html: Optional[str] = None,      # Current draft HTML for incremental edits
    previous_spec: Optional[str] = None,       # Previous spec used to generate existing_html
) -> tuple[Optional[str], dict]:
```

- When `existing_html` is provided (and non-empty), the method uses Mode B (incremental edit).
- When `existing_html` is `None` or empty, the method uses Mode A (fresh generation).

---

## 6. Layout Integrity: No Internal Scrollbars

Visualizations must be sized to fit their container cleanly. Internal scrollbars on visual elements (charts, panels, cards, sidebars) break the communication of ideas and indicate a layout problem. They must be prevented.

### 6.1 Root Cause

Internal scrollbars appear when a container has a fixed pixel height that is smaller than its content, combined with `overflow: auto` or `overflow: scroll`. This is especially common with chart wrappers and data panels.

### 6.2 Required CSS Rules

Every generated HTML document must:

1. **Set the root to fill the viewport without overflow:**
   ```css
   *, *::before, *::after { box-sizing: border-box; }
   html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }
   ```

2. **Use viewport-relative sizing for the main container:** The top-level layout container should use `height: 100vh` (or `min-height: 100vh` if content may be taller) and `width: 100vw`. Never use a fixed pixel height for the root container.

3. **Avoid `overflow: auto/scroll` on visual sub-elements:** Chart containers, panels, cards, and sidebars must use `overflow: hidden` or `overflow: visible`. If content might not fit, it should be scaled or simplified, not made scrollable.

4. **Size charts and panels proportionally:** Use percentage-based heights relative to their parent, or use `flex: 1` / `min-height: 0` patterns within flex columns so children fill available space without overflowing.

5. **Never hardcode pixel heights smaller than expected content:** If a container must have a fixed height, it must be large enough to contain its content at all expected data sizes. When in doubt, use `min-height` instead of `height`.

### 6.3 Acceptable Exception

The one acceptable scrollable area is the **`<body>` itself** for visualizations that are intentionally long/scrollable (e.g., a long infographic or report). In that case, `body { overflow: auto }` is acceptable, but no sub-element should independently scroll.

### 6.4 Impact on Prompts

Both `HTML_GENERATION_SYSTEM_PROMPT` and `HTML_INCREMENTAL_EDIT_SYSTEM_PROMPT` must include an explicit "No Internal Scrollbars" directive with the CSS rules above.

---

## 7. Mobile-Friendly Layouts

All generated visualizations must work correctly and look good on mobile screen sizes, not just desktop. The visualization is rendered in an iframe; the host page may be viewed on any device.

### 7.1 Required `<meta>` Tag

Every generated HTML document must include the viewport meta tag in `<head>`:

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

Without this tag, mobile browsers render the page at desktop width and scale it down, making text and controls unreadable.

### 7.2 Responsive Layout Rules

1. **Use fluid widths by default.** All containers, charts, and panels must use `width: 100%` or percentage widths rather than fixed pixel widths.

2. **Use CSS media queries for layout changes.** At a minimum, target `max-width: 600px` for mobile:
   - Switch multi-column flex/grid layouts to single-column
   - Reduce font sizes (headings, labels, legends)
   - Reduce padding and margins
   - Simplify or hide secondary elements (e.g., collapse a sidebar into a toggle or drop it)

3. **Size charts responsively.** Charts (D3, Chart.js, Plotly) must not use fixed pixel widths. Use `100%` width and derive height from the container or a percentage of `100vh`.

4. **Touch-friendly interaction targets.** Any interactive element (button, legend item, tooltip trigger, node) must be at least 44×44px on mobile. Hover-only interactions should have a tap/click fallback.

5. **Readable text at small sizes.** Body text must be at least `14px` and chart labels at least `11px`. Axis tick labels should be rotated or reduced in count when there is insufficient horizontal space on mobile.

6. **Avoid horizontal overflow.** No element may cause the page to scroll horizontally. Test the layout mentally at 375px (iPhone SE) and 768px (tablet) widths.

### 7.3 Library-Specific Guidance

- **D3.js**: Use `ResizeObserver` or derive SVG dimensions from `element.getBoundingClientRect()` rather than hardcoded `width`/`height` constants. Re-render or rescale on resize.
- **Chart.js**: Set `responsive: true` and `maintainAspectRatio: false` on all chart instances. Let the container control the size.
- **Plotly.js**: Use `responsive: true` in the config object and `width: null` in layout so Plotly fills the container.
- **Mermaid.js**: Wrap the diagram in a `width: 100%; overflow-x: auto` container. Mermaid SVGs are naturally fluid.

### 7.4 Impact on Prompts

Both `HTML_GENERATION_SYSTEM_PROMPT` and `HTML_INCREMENTAL_EDIT_SYSTEM_PROMPT` must include an explicit "Mobile-Friendly Layout" directive covering the viewport meta tag, fluid widths, media queries, touch targets, and library-specific responsive settings.

---

## 8. Viewing Historical Draft Versions from Chat

Each `html_output` message in the chat history represents a distinct generation of the visualization. When a user clicks on one of these messages in the chat view, they must see **that specific version's HTML**, not the `current_draft_html` (which is always the latest).

### 8.1 Navigation from Chat

When the user clicks a visualization link inside a chat `html_output` message, the router must include the originating message ID as a query parameter:

```
/visualization/:vizId?msgId=<message_id>
```

### 8.2 Behavior in VisualizationView

On mount, `VisualizationView` checks for the `msgId` query parameter:

- **`msgId` absent**: Normal mode — display `current_draft_html`.
- **`msgId` present**: Draft history mode — fetch the chat session, locate the `html_output` message with the matching `message_id`, and display **that message's HTML** in the iframe instead of `current_draft_html`.

In draft history mode:
- The iframe renders the historical HTML (not the latest draft).
- A "Viewing historical draft" indicator is shown.
- A "Back to current draft" button is available to clear the override.
- The back-arrow still navigates to `/chat/:vizId` (not the dashboard), since the user arrived from the chat screen.

### 8.3 Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `ChatMessage.vue` | Append `?msgId=<message_id>` when navigating to `/visualization/:vizId` |
| `VisualizationView.vue` | Read `msgId` from route query on mount; fetch chat session; resolve and display message HTML |

---

## 9. Summary of Changes Required

| File | Change |
|------|--------|
| `backend/app/services/llm_service.py` | Update `HTML_GENERATION_SYSTEM_PROMPT` with richness directives || `backend/app/services/llm_service.py` | Update `HTML_GENERATION_SYSTEM_PROMPT` with no-internal-scrollbar directive |
| `backend/app/services/llm_service.py` | Update `HTML_INCREMENTAL_EDIT_SYSTEM_PROMPT` with no-internal-scrollbar directive || `backend/app/services/llm_service.py` | Update `generate_html_from_spec` signature to accept `existing_html` and `previous_spec` |
| `backend/app/services/llm_service.py` | Implement Mode A vs Mode B prompt construction |
| `backend/app/services/llm_service.py` | Set `max_tokens=80000` for HTML generation |
| `backend/app/routers/chat.py` | Pass `current_draft_html` and `current_draft_spec` to `generate_html_from_spec` when available |
| `frontend/src/components/chat/ChatMessage.vue` | Pass `?msgId=<message_id>` query param when navigating to visualization view |
| `frontend/src/views/VisualizationView.vue` | On mount, resolve `msgId` query param to a specific chat message's HTML and display it |
