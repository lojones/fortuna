import logging
from typing import Optional

import anthropic
from fastapi import WebSocket

from app.config import settings
from app.models.chat import ChatSessionInDB

logger = logging.getLogger(__name__)

# Pricing constants for claude-opus-4-6 ($5/MTok input, $25/MTok output)
_INPUT_COST_PER_TOKEN = 5.0 / 1_000_000    # $5 / million tokens
_OUTPUT_COST_PER_TOKEN = 25.0 / 1_000_000  # $25 / million tokens
_EMPTY_USAGE: dict = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}


def _compute_cost(input_tokens: int, output_tokens: int) -> dict:
    cost = input_tokens * _INPUT_COST_PER_TOKEN + output_tokens * _OUTPUT_COST_PER_TOKEN
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost, 6),
    }


async def _safe_send(websocket: WebSocket, data: dict) -> bool:
    """Send JSON to WebSocket, returning False if the client disconnected."""
    try:
        await websocket.send_json(data)
        return True
    except Exception:
        return False


# Phase 1: Clarification — only asks questions, then produces a spec
CLARIFICATION_SYSTEM_PROMPT = """You are Fortuna's visualization assistant. Your job is to understand \
exactly what the user wants to visualize through a conversational exchange.

RULES:
1. Ask targeted clarifying questions (ONE to THREE at a time) to understand:
   - What data or information to visualize
   - Desired chart/visualization type (bar, line, diagram, infographic, dashboard, etc.)
   - Specific data points, labels, colors, and styles
   - The story or insight the visualization should convey
   - Any interactivity requirements

2. NEVER generate HTML, code, or code blocks. You are ONLY having a conversation.

3. When you have gathered enough detail to fully specify the visualization, respond with \
EXACTLY this marker on its own line, followed by a detailed text specification:

<<<SPEC_READY>>>
[Write an EXTREMELY detailed and comprehensive plain-text specification for the visualization. \
This spec is the ONLY input the HTML generator will receive — it will never see the conversation — \
so every single detail must be captured here. Leave nothing implicit or assumed.

The spec MUST exhaustively cover ALL of the following:
- Page layout and structure (sections, panels, columns, header/footer)
- Every data point, value, label, and category — list them explicitly
- Chart/visualization types and configurations (axes, scales, ranges, tick marks)
- Complete color palette with exact hex codes or descriptive names for every element
- Typography: font families, sizes, weights, line heights for headings, body, labels
- Spacing, padding, margins, and alignment
- Legends, tooltips, annotations, and callouts
- Interactivity: hover effects, click behaviors, transitions, animations
- Responsive behavior and breakpoints
- Edge cases: empty states, overflow handling, long text truncation
- Any icons, decorative elements, or visual flourishes
- Accessibility considerations (contrast, ARIA labels)

Be verbose. A 2,000+ word spec is expected for any non-trivial visualization. \
The more detail you provide, the better the resulting visualization will be.]

The specification must be detailed enough that a developer could build the visualization \
from it alone, without any further questions and without seeing any of the conversation history.

4. When the user asks you to edit or refine an existing visualization, look at the current \
spec (provided in context) and ask only the questions needed to understand the changes. \
Then output <<<SPEC_READY>>> with the COMPLETE updated specification (not just the diff).
"""

# Phase 2: HTML generation from spec (non-streaming, internal)
HTML_GENERATION_SYSTEM_PROMPT = """You are an expert HTML/CSS/JavaScript developer. \
You receive a detailed visualization specification and produce a complete, self-contained \
HTML document that implements it exactly.

RULES:
- Output ONLY the complete HTML document. No explanations, no markdown fences, no commentary.
- Start with <!DOCTYPE html>
- All CSS and JavaScript must be inline in the document.
- The visualization must render correctly in a sandboxed iframe.
- Use modern CSS (flexbox, grid) for layout.

CREATIVE LIBRARY USE — Be ambitious and expressive:
- You MUST actively choose the most visually expressive tool for the job. Never default to plain
  HTML/CSS if a richer approach is available.
- Prefer library-based, interactive, animated visualizations over static markup whenever the data
  or content supports it.
- Available libraries and their ideal uses:
  * D3.js (cdnjs/jsdelivr): Custom charts, network/force graphs, hierarchical layouts, tree diagrams,
    geographic maps, SVG animations, any visualization needing fine-grained visual control.
  * Chart.js (cdnjs/jsdelivr): Clean standard charts — bar, line, pie, radar, doughnut — for dashboards.
  * Plotly.js (cdn.plot.ly): Scientific charts, 3D plots, statistical distributions, financial charts.
  * Mermaid.js (cdn.jsdelivr.net): Flow diagrams, sequence diagrams, Gantt charts, ER diagrams,
    state machines, org charts, Git graphs — any process or relationship diagram.
  * Plain SVG + CSS animations: Infographics, process diagrams, icon-heavy layouts, decorative elements.
- Layer libraries when appropriate: e.g., D3 for the main chart plus Mermaid for a workflow sidebar.
- Use animations purposefully: entrance animations, state transitions, hover micro-interactions.
- AVOID plain HTML tables and bullet lists for data that could be a chart, diagram, or visual layout.
  Only use tables/lists when tabular or sequential structure is genuinely the clearest format.
- Load all libraries from official, stable CDN URLs (cdnjs, jsdelivr, unpkg, cdn.plot.ly).

QUALITY DIRECTIVES — Maximize detail and richness:
- Generate the most thorough, polished, and complete implementation possible.
- Every aspect of the specification MUST be fully realized, never abbreviated or simplified.
- Use your full output capacity. Do NOT produce a minimal working version.
- Invest heavily in:
  * Rich CSS styling: gradients, box-shadows, transitions, hover/focus effects, animations
  * Comprehensive interactivity: tooltips, click handlers, smooth animations, state transitions
  * Thorough data rendering: ALL data points, labels, legends, annotations, axis titles
  * Mobile-friendly, responsive layout (see MOBILE-FRIENDLY LAYOUT section below)
  * Accessibility: aria-labels, semantic HTML elements, keyboard navigation where appropriate
  * Inline comments explaining major sections of the code
- NEVER use placeholder data, "..." ellipsis, or TODO markers. Every element in the spec must be present.
- If the spec describes 50 data points, render all 50. If it describes 10 sections, build all 10.

NO INTERNAL SCROLLBARS — Critical layout rule:
- Internal scrollbars on panels, charts, cards, or any sub-element are strictly forbidden.
- Every generated document MUST include these root CSS rules:
    *, *::before, *::after { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }
- The top-level layout container must use height: 100vh (or min-height: 100vh) and width: 100vw.
- NEVER use overflow: auto or overflow: scroll on any visual sub-element (charts, panels, cards, sidebars).
  Use overflow: hidden or overflow: visible instead.
- Size chart containers and panels with percentage heights, flex: 1, or min-height: 0 so they fill
  available space proportionally without overflowing.
- NEVER hardcode a fixed pixel height on a container that might be smaller than its content.
  Use min-height instead of height when the content size is uncertain.
- Exception: body { overflow-y: auto } is acceptable ONLY for intentionally long/scrollable infographics
  where the full page scrolls. In that case remove overflow: hidden from body only, and still
  ensure no sub-element scrolls independently.

MOBILE-FRIENDLY LAYOUT — Required for all visualizations:
- Include this in every <head>: <meta name="viewport" content="width=device-width, initial-scale=1.0">
- Use fluid widths: all containers, charts, and panels must use width: 100% or percentage widths,
  never fixed pixel widths.
- Include CSS media queries targeting at minimum max-width: 600px that:
  * Switch multi-column flex/grid layouts to a single column
  * Reduce font sizes (headings, axis labels, legends) proportionally
  * Reduce padding and margins to maximize usable space
  * Simplify or hide secondary decorative elements
- Size all charts responsively:
  * D3.js: derive SVG width/height from the container element, not hardcoded constants
  * Chart.js: set responsive: true and maintainAspectRatio: false on every chart instance
  * Plotly.js: set responsive: true in the config and width: null in the layout
  * Mermaid.js: wrap in a container with width: 100%; overflow-x: hidden
- Touch targets: any interactive element (button, legend, node, tooltip trigger) must be at
  least 44x44px on mobile; hover-only behaviours must have a tap/click fallback.
- Minimum text sizes: body text >= 14px, chart/axis labels >= 11px on mobile.
- Horizontal overflow is forbidden: no element may cause the page to scroll horizontally.
"""

# System prompt addendum for incremental edits (Mode B)
HTML_INCREMENTAL_EDIT_SYSTEM_PROMPT = """You are an expert HTML/CSS/JavaScript developer. \
You receive an existing HTML visualization, the previous specification it was built from, \
and an updated specification. Your job is to surgically update the existing HTML to reflect \
ONLY the changes between the previous and updated specifications.

RULES:
- Output ONLY the complete updated HTML document. No explanations, no markdown fences, no commentary.
- Start with <!DOCTYPE html>
- Keep as much of the existing HTML, CSS, and JavaScript UNCHANGED as possible.
- Only modify the sections directly affected by the spec differences.
- Preserve ALL existing:
  * Visual styling (colors, fonts, gradients, shadows, spacing)
  * Layout structure and CSS rules
  * JavaScript logic and interactivity that is not affected by the changes
  * Comments and code organization
  * Library choices (D3, Chart.js, Mermaid, Plotly, etc.)
- If the spec adds new elements, integrate them seamlessly with the existing style and structure.
  Prefer the same library already in use; introduce a new library only if the new element genuinely
  requires capabilities the existing libraries lack.
- If the spec removes elements, remove them cleanly without leaving orphaned styles or scripts.
- If the spec modifies data, update only the affected data while keeping rendering logic intact.
- The output must be a COMPLETE HTML document, not a diff or patch.
- Load all libraries from official, stable CDN URLs (cdnjs, jsdelivr, unpkg, cdn.plot.ly).

CREATIVE LIBRARY USE — Maintain and enhance visual ambition:
- Preserve the library-based, interactive, animated approach of the original.
- If the existing visualization uses D3, Chart.js, Mermaid, or Plotly, keep using them for the
  updated/added elements. Match the same level of visual richness.
- If new content is added that the current library handles poorly, you may introduce an additional
  library, but only alongside the existing ones — never replace them.
- AVOID plain HTML tables and bullet lists for data that could be a chart, diagram, or visual layout.

QUALITY DIRECTIVES:
- Maintain the same level of detail and polish as the original.
- Every aspect of the updated specification MUST be fully realized.
- NEVER use placeholder data, "..." ellipsis, or TODO markers.

NO INTERNAL SCROLLBARS — Critical layout rule:
- Internal scrollbars on panels, charts, cards, or any sub-element are strictly forbidden.
- Preserve or add these root CSS rules:
    *, *::before, *::after { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }
- NEVER use overflow: auto or overflow: scroll on any visual sub-element.
- If the existing HTML already violates this rule, fix the offending elements as part of the update.
- Exception: body { overflow-y: auto } is acceptable ONLY for intentionally long/scrollable infographics.

MOBILE-FRIENDLY LAYOUT — Preserve and enhance:
- Ensure <meta name="viewport" content="width=device-width, initial-scale=1.0"> is present in <head>.
- All containers, charts, and panels must use fluid (percentage) widths, not fixed pixel widths.
- Preserve any existing media queries; add or fix them if the update changes layout structure.
- Keep chart library responsive settings intact:
  * D3.js: container-derived dimensions, not hardcoded constants
  * Chart.js: responsive: true and maintainAspectRatio: false
  * Plotly.js: responsive: true in config, width: null in layout
  * Mermaid.js: width: 100%; overflow-x: hidden wrapper
- Interactive elements must remain touch-friendly (min 44x44px) on mobile.
- If the existing HTML violates mobile rules, fix the violations as part of the update.
- Horizontal overflow is forbidden: no element may cause the page to scroll horizontally.
"""


class LLMService:
    def __init__(self):
        logger.info("LLMService.__init__: initializing Anthropic async client")
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def process_message(
        self,
        session: ChatSessionInDB,
        new_user_message: str,
        websocket: WebSocket,
        current_spec: Optional[str] = None,
    ) -> tuple[str, bool, Optional[str], dict]:
        """
        Phase 1: Clarification conversation.
        Returns: (assistant_response_text, is_spec_ready, spec_text_or_none, usage_dict)
        Streams clarification response tokens to websocket in real time.
        """
        logger.info(f"process_message: START session_id={session.id}, history={len(session.messages)} msgs, has_spec={bool(current_spec)}")
        logger.debug(f"process_message: user message ({len(new_user_message)} chars): '{new_user_message[:100]}{'...' if len(new_user_message) > 100 else ''}'")

        # Build message history for Claude
        messages = []
        for msg in session.messages:
            if msg.message_type == "spec_output":
                # Summarize instead of replaying large content
                messages.append({
                    "role": "assistant",
                    "content": "[A visualization specification was generated. User is now requesting changes.]",
                })
            elif msg.role in ("user", "assistant"):
                messages.append({"role": msg.role, "content": msg.content})

        # Ensure messages alternate properly
        cleaned = []
        for msg in messages:
            if cleaned and cleaned[-1]["role"] == msg["role"]:
                cleaned[-1]["content"] += "\n\n" + msg["content"]
            else:
                cleaned.append(msg)

        if cleaned and cleaned[0]["role"] != "user":
            cleaned.insert(0, {"role": "user", "content": "(Starting conversation)"})

        messages = cleaned

        # If there's an existing spec, prepend context so the LLM knows
        system_prompt = CLARIFICATION_SYSTEM_PROMPT
        if current_spec:
            system_prompt += f"\n\nCURRENT VISUALIZATION SPEC (for reference if user wants edits):\n---\n{current_spec}\n---"

        logger.debug(f"Sending {len(messages)} messages to Claude (clarification phase)")

        # Stream from Claude
        full_response = ""
        chunk_count = 0
        # Buffer to prevent partial marker text from reaching the client.
        # We hold back up to len(MARKER)-1 chars until we're sure they're not
        # the start of the <<<SPEC_READY>>> marker.
        MARKER = "<<<SPEC_READY>>>"
        pending = ""   # chars not yet sent
        marker_sent = False  # once marker found, stop sending entirely
        usage_data = _EMPTY_USAGE
        try:
            logger.debug("Opening Claude streaming connection (clarification)")
            async with self.client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=25000,
                system=system_prompt,
                messages=messages,
            ) as stream:
                async for text_chunk in stream.text_stream:
                    full_response += text_chunk
                    chunk_count += 1
                    if not marker_sent:
                        pending += text_chunk
                        if MARKER in pending:
                            # Notify client that spec is being built (triggers its own progress bar)
                            await _safe_send(websocket, {"type": "spec_streaming"})
                            marker_sent = True
                            parts_at_marker = pending.split(MARKER, 1)
                            safe = parts_at_marker[0]
                            if safe:
                                await _safe_send(websocket, {"type": "chunk", "content": safe})
                            # Stream the spec content that arrived after the marker in this chunk
                            spec_part = parts_at_marker[1]
                            if spec_part:
                                await _safe_send(websocket, {"type": "spec_chunk", "content": spec_part})
                            pending = ""
                        else:
                            # Send all but the last len(MARKER)-1 chars
                            safe_end = len(pending) - (len(MARKER) - 1)
                            if safe_end > 0:
                                await _safe_send(websocket, {"type": "chunk", "content": pending[:safe_end]})
                                pending = pending[safe_end:]
                    else:
                        # Spec is streaming — forward each chunk to the client
                        await _safe_send(websocket, {"type": "spec_chunk", "content": text_chunk})
                # Capture token usage before closing the stream context
                final_msg = await stream.get_final_message()
                usage_data = _compute_cost(final_msg.usage.input_tokens, final_msg.usage.output_tokens)
            # Flush any remaining buffered text if no marker was found
            if not marker_sent and pending:
                await _safe_send(websocket, {"type": "chunk", "content": pending})
            logger.info(
                f"Claude clarification stream complete: {chunk_count} chunks, "
                f"{len(full_response)} total chars, "
                f"in={usage_data['input_tokens']} out={usage_data['output_tokens']} "
                f"cost=${usage_data['cost_usd']:.4f}"
            )
        except anthropic.APIStatusError as e:
            logger.error(f"Anthropic API error (status={e.status_code}): {e.message}", exc_info=True)
            await _safe_send(websocket, {
                "type": "error",
                "message": f"LLM API error: {str(e)}",
            })
            return (full_response or "An error occurred.", False, None, _EMPTY_USAGE)
        except Exception as e:
            logger.error(f"Unexpected error during LLM streaming: {e}", exc_info=True)
            await _safe_send(websocket, {
                "type": "error",
                "message": "An unexpected error occurred during generation.",
            })
            return (full_response or "An error occurred.", False, None, _EMPTY_USAGE)

        # Check if spec is ready
        if "<<<SPEC_READY>>>" in full_response:
            logger.info("SPEC_READY marker detected in response")
            parts = full_response.split("<<<SPEC_READY>>>", 1)
            pre_text = parts[0].strip()
            spec_text = parts[1].strip()

            if spec_text:
                logger.info(f"Specification extracted: {len(spec_text)} chars")
                # Send a status update to the client (not the spec itself)
                if pre_text:
                    # The pre-text was already streamed; send complete for that part
                    pass
                await _safe_send(websocket, {"type": "complete", "usage": usage_data})
                await _safe_send(websocket, {
                    "type": "status",
                    "message": "Generating visualization...",
                })
                return (pre_text, True, spec_text, usage_data)
            else:
                logger.warning("SPEC_READY marker present but spec text empty. Treating as clarification.")
                await _safe_send(websocket, {"type": "complete", "usage": usage_data})
                return (full_response, False, None, usage_data)
        else:
            logger.info(f"Clarification response: {len(full_response)} chars, no spec ready")
            await _safe_send(websocket, {"type": "complete", "usage": usage_data})
            return (full_response, False, None, usage_data)

    async def generate_html_from_spec(
        self,
        spec_text: str,
        websocket: WebSocket,
        existing_html: Optional[str] = None,
        previous_spec: Optional[str] = None,
    ) -> tuple[Optional[str], dict]:
        """
        Phase 2: Generate HTML/JS from a text specification.
        Returns: (html_content_or_none, usage_dict)
        Uses streaming to avoid the 10-minute non-streaming timeout.
        Accumulates the full response, then validates and sends it.

        Supports two modes:
          Mode A (fresh): existing_html is None — generates from scratch.
          Mode B (incremental): existing_html provided — edits existing HTML
            using the delta between previous_spec and spec_text.
        """
        is_incremental = bool(existing_html and existing_html.strip())
        mode_label = "incremental edit" if is_incremental else "fresh generation"
        logger.info(f"generate_html_from_spec: START mode={mode_label} spec_length={len(spec_text)} chars")
        if is_incremental:
            logger.info(f"  existing_html={len(existing_html or '')} chars, previous_spec={len(previous_spec or '')} chars")

        # Choose system prompt and user message based on mode
        if is_incremental:
            system_prompt = HTML_INCREMENTAL_EDIT_SYSTEM_PROMPT
            user_content = (
                "The user has updated the visualization specification. "
                "Update the existing HTML to reflect ONLY the changes in the new specification. "
                "Keep all other HTML, CSS, JavaScript, styling, layout, colors, and structure exactly the same.\n\n"
                "=== EXISTING HTML DOCUMENT ===\n"
                f"{existing_html}\n\n"
            )
            if previous_spec:
                user_content += (
                    "=== PREVIOUS SPECIFICATION ===\n"
                    f"{previous_spec}\n\n"
                )
            user_content += (
                "=== UPDATED SPECIFICATION ===\n"
                f"{spec_text}\n\n"
                "Apply ONLY the differences between the previous and updated specifications "
                "to the existing HTML document. Output the complete updated HTML document."
            )
        else:
            system_prompt = HTML_GENERATION_SYSTEM_PROMPT
            user_content = (
                "Generate a complete, highly detailed HTML visualization from this specification. "
                "Use your full output capacity to create the richest, most polished implementation possible. "
                "Do not abbreviate or simplify — implement every detail described in the spec.\n\n"
                f"{spec_text}"
            )

        usage_data = _EMPTY_USAGE
        try:
            html_content = ""
            chunk_count = 0
            async with self.client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=80000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_content,
                    }
                ],
            ) as stream:
                async for text_chunk in stream.text_stream:
                    html_content += text_chunk
                    chunk_count += 1
                    # Forward each chunk to the client for live viewing
                    await _safe_send(websocket, {"type": "html_chunk", "content": text_chunk})
                # Capture token usage before closing the stream context
                final_msg = await stream.get_final_message()
                usage_data = _compute_cost(final_msg.usage.input_tokens, final_msg.usage.output_tokens)

            logger.info(
                f"HTML stream complete: {chunk_count} chunks, {len(html_content)} chars, "
                f"in={usage_data['input_tokens']} out={usage_data['output_tokens']} "
                f"cost=${usage_data['cost_usd']:.4f}"
            )

            html_content = html_content.strip()

            # Strip markdown fences if the model wrapped it
            if html_content.startswith("```html"):
                html_content = html_content[len("```html"):].strip()
            if html_content.startswith("```"):
                html_content = html_content[3:].strip()
            if html_content.endswith("```"):
                html_content = html_content[:-3].strip()

            # Validate
            if html_content.lower().startswith("<!doctype") or html_content.lower().startswith("<html"):
                logger.info(f"HTML generated successfully: {len(html_content)} chars")
                await _safe_send(websocket, {
                    "type": "visualization_ready",
                    "html": html_content,
                    "spec": spec_text,
                    "usage": usage_data,
                })
                return (html_content, usage_data)
            else:
                logger.warning(f"Generated content doesn't look like HTML (starts with: '{html_content[:80]}')")
                await _safe_send(websocket, {
                    "type": "error",
                    "message": "Failed to generate valid HTML. Please try refining your description.",
                })
                return (None, usage_data)

        except anthropic.APIStatusError as e:
            logger.error(f"Anthropic API error during HTML generation: {e.message}", exc_info=True)
            await _safe_send(websocket, {
                "type": "error",
                "message": f"HTML generation failed: {str(e)}",
            })
            return (None, _EMPTY_USAGE)
        except Exception as e:
            logger.error(f"Unexpected error during HTML generation: {e}", exc_info=True)
            await _safe_send(websocket, {
                "type": "error",
                "message": "An unexpected error occurred during HTML generation.",
            })
            return (None, _EMPTY_USAGE)


llm_service = LLMService()
