# SPEC2: Increase Spec Detail — Larger Context Window + Prompt Update

## Problem

The Phase 1 (clarification / spec-building) LLM call in `llm_service.py` currently uses `max_tokens=16000`, and the system prompt doesn't strongly emphasize producing a highly detailed specification. This limits the depth of the generated spec, which in turn limits the quality of the HTML visualization produced in Phase 2. The spec should be as exhaustively detailed as possible to give the HTML generation phase comprehensive instructions.

## Required Changes

### Change 1: Increase `max_tokens` from 16,000 to 25,000

#### Affected File: `backend/app/services/llm_service.py` — `process_message` method

```python
# BEFORE (around line 138)
async with self.client.messages.stream(
    model="claude-opus-4-6",
    max_tokens=16000,
    system=system_prompt,
    messages=messages,
) as stream:

# AFTER
async with self.client.messages.stream(
    model="claude-opus-4-6",
    max_tokens=25000,
    system=system_prompt,
    messages=messages,
) as stream:
```

---

### Change 2: Update `CLARIFICATION_SYSTEM_PROMPT` to demand a highly detailed spec

The current prompt says "Write a thorough plain-text specification" but does not strongly emphasize exhaustive detail, granularity, or length. The spec is the sole input to Phase 2 — the HTML generator never sees the original conversation — so omissions here directly cause missing features in the output.

#### Affected File: `backend/app/services/llm_service.py` — `CLARIFICATION_SYSTEM_PROMPT`

```python
# BEFORE
<<<SPEC_READY>>>
[Write a thorough plain-text specification describing every aspect of the visualization: \
layout, data, colors, fonts, chart types, labels, legends, interactivity, responsive behavior, \
and any other relevant details. This spec will be used by a separate process to generate the HTML.]

The specification should be detailed enough that a developer could build the visualization \
from it alone, without any further questions.

# AFTER
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
```

---

## Context Summary

| Phase | Purpose | Current `max_tokens` | New `max_tokens` |
|-------|---------|---------------------|-------------------|
| Phase 1 — `process_message` | Clarification + spec generation | 16,000 | **25,000** |
| Phase 2 — `generate_html_from_spec` | HTML/JS generation from spec | 40,000 | 40,000 (unchanged) |

## Notes

- The `max_tokens` change only affects output token budget. It does not change the model's input context window.
- The prompt change reinforces that the spec is the **sole bridge** between the conversation and HTML generation — the HTML generator has zero access to the chat history.
- Larger specs will increase Phase 2 input token cost since the full spec is sent as the prompt for HTML generation. This is an acceptable trade-off for higher-quality output.
- The explicit checklist in the prompt ensures the LLM doesn't skip categories of detail it might otherwise abbreviate.
- No frontend changes required.
