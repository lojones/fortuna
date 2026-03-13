# Frontend Tweaks Specification

## Version 1.0.0

---

## 1. Cost Display Rounding

### Problem
Cost dollar values are displayed with excessive precision (4–6 decimal places). Small sub-cent values show confusing amounts like `$0.000312`. The display should be simplified to cents.

### Current Behavior
- `formatCost()` in [ChatMessage.vue](frontend/src/components/chat/ChatMessage.vue) shows 4–6 decimal places depending on magnitude.
- `formatTotalCost()` in [ChatView.vue](frontend/src/views/ChatView.vue) shows 2–6 decimal places depending on magnitude.
- Both functions are used to render per-message cost and the header total cost badge.

### Required Behavior
- All cost dollar values displayed in the UI **must be rounded to the nearest cent** (2 decimal places).
- Any cost value **under $0.01 must be rounded up to $0.01** (i.e., `Math.max(0.01, ...)`), so the minimum displayed cost is always `$0.01`.
- Zero-cost values (`0` or `null`) should continue to not be displayed (existing `v-if` guards handle this).

### Affected Files

#### `frontend/src/components/chat/ChatMessage.vue`

Replace the `formatCost` function:

```javascript
// BEFORE
function formatCost(usd) {
  if (usd == null) return ''
  if (usd >= 0.01) return usd.toFixed(4)
  if (usd >= 0.0001) return usd.toFixed(5)
  return usd.toFixed(6)
}

// AFTER
function formatCost(usd) {
  if (usd == null || usd === 0) return ''
  const rounded = Math.max(0.01, Math.round(usd * 100) / 100)
  return rounded.toFixed(2)
}
```

#### `frontend/src/views/ChatView.vue`

Replace the `formatTotalCost` function:

```javascript
// BEFORE
function formatTotalCost(usd) {
  if (usd >= 1) return usd.toFixed(2)
  if (usd >= 0.01) return usd.toFixed(4)
  if (usd >= 0.0001) return usd.toFixed(5)
  return usd.toFixed(6)
}

// AFTER
function formatTotalCost(usd) {
  if (usd == null || usd === 0) return ''
  const rounded = Math.max(0.01, Math.round(usd * 100) / 100)
  return rounded.toFixed(2)
}
```

### Display Examples

| Raw Value     | Displayed |
|---------------|-----------|
| `0.0003`      | `$0.01`   |
| `0.0089`      | `$0.01`   |
| `0.0150`      | `$0.02`   |
| `0.0349`      | `$0.03`   |
| `0.2567`      | `$0.26`   |
| `1.4321`      | `$1.43`   |
| `0`           | *(hidden)*|
| `null`        | *(hidden)*|

---

## 2. Spec Progress Bar: Show Token In/Out and Cost After Refresh

### MongoDB Chat Message Schema

Cost data is persisted to MongoDB as part of each `ChatMessage` document stored in the `chat_sessions` collection. The `ChatMessage` Pydantic model (and therefore every MongoDB document in the `messages` array) includes the following optional cost fields:

```python
class ChatMessage(BaseModel):
    message_id: str
    role: Literal["user", "assistant"]
    content: str
    message_type: Literal["chat", "clarification", "html_output", "spec_output"]
    timestamp: datetime
    input_tokens: Optional[int] = None    # tokens sent to the LLM API
    output_tokens: Optional[int] = None   # tokens returned by the LLM API
    cost_usd: Optional[float] = None      # USD cost of the API call
```

**Persistence requirement:** Every assistant message that results from an LLM API call **must** have `input_tokens`, `output_tokens`, and `cost_usd` written to MongoDB when the message is stored. This ensures cost data survives page refreshes and can be summed to compute `totalSessionCost` from the stored session without relying on in-memory state.

| Message type | LLM phase | Must store cost fields |
|---|---|---|
| `clarification` (standalone, no spec) | Phase 1 | ✅ Yes |
| `clarification` (pre-text before spec) | Phase 1 | ❌ No — cost attached to `spec_output` instead (see below) |
| `spec_output` | Phase 1 | ✅ Yes |
| `html_output` | Phase 2 | ✅ Yes |
| `chat` (user messages) | — | ❌ N/A |

### Problem
When a chat is resumed (page refresh or navigating back to `/chat/:vizId`), the **spec-building progress bar** (rendered for `spec_output` messages) does not display the token in/out count or cost — even though the **HTML generation progress bar** (`html_output` messages) does. This is because:

1. **Backend:** The `spec_output` message is saved to MongoDB **without** `input_tokens`, `output_tokens`, or `cost_usd` fields. The phase 1 usage data is incorrectly attached only to the pre-text clarification message (if one exists), not to the `spec_output` message itself. This violates the persistence requirement above and causes the data to be lost on refresh.
2. **Frontend (store):** When `onVisualizationReady` fires in [chat.js](frontend/src/stores/chat.js), the `spec_output` message is pushed to the local session without usage data.
3. **Frontend (component):** The `spec_output` template block in [ChatMessage.vue](frontend/src/components/chat/ChatMessage.vue) does not include a section displaying token/cost info, unlike the `html_output` block which does.

### Required Behavior
- All cost data for every LLM API call **must be written to MongoDB** on the message that semantically owns that call (see schema table above).
- After page refresh, the **spec-building completed progress bar** must display token in/out counts and cost, identical in format to how the HTML generation progress bar displays them.
- During live streaming, the usage data must also be attached to the `spec_output` message when it is pushed into the local session state.

### Affected Files

#### `backend/app/routers/chat.py`

Attach phase 1 usage data to the `spec_output` message when storing it in the database.

```python
# BEFORE (around line 152)
spec_msg = ChatMessage(
    message_id=str(uuid.uuid4()),
    role="assistant",
    content=spec_text,
    message_type="spec_output",
    timestamp=datetime.now(timezone.utc),
)

# AFTER
spec_msg = ChatMessage(
    message_id=str(uuid.uuid4()),
    role="assistant",
    content=spec_text,
    message_type="spec_output",
    timestamp=datetime.now(timezone.utc),
    input_tokens=phase1_usage["input_tokens"],
    output_tokens=phase1_usage["output_tokens"],
    cost_usd=phase1_usage["cost_usd"],
)
```

**Note:** When a pre-text clarification message also exists (i.e., `response_text` is non-empty), the usage data is currently duplicated onto that message. Since the usage represents the entire phase 1 API call, it should be attached **only** to the `spec_output` message to avoid double-counting in the `totalSessionCost` computation. Remove the usage fields from the `pre_msg`:

```python
# BEFORE
pre_msg = ChatMessage(
    message_id=str(uuid.uuid4()),
    role="assistant",
    content=response_text,
    message_type="clarification",
    timestamp=datetime.now(timezone.utc),
    input_tokens=phase1_usage["input_tokens"],
    output_tokens=phase1_usage["output_tokens"],
    cost_usd=phase1_usage["cost_usd"],
)

# AFTER
pre_msg = ChatMessage(
    message_id=str(uuid.uuid4()),
    role="assistant",
    content=response_text,
    message_type="clarification",
    timestamp=datetime.now(timezone.utc),
)
```

#### `frontend/src/stores/chat.js`

In the `onVisualizationReady` handler, attach the phase 1 usage data to the `spec_output` message that is pushed into the local session. The `usage` parameter passed to this handler is the phase 2 (HTML generation) usage. The phase 1 (spec) usage needs to be captured separately.

Add a new handler `onSpecComplete` to receive phase 1 usage and store it, then use it when pushing the `spec_output` message:

```javascript
// Add state to hold phase 1 usage temporarily
const specUsage = ref(null)

// In connectToChat handlers, add:
onComplete(usage) {
  // ... existing code ...
  // Also store as specUsage when a spec was just built
  if (usage) {
    specUsage.value = usage
  }
}

// In onVisualizationReady, update the spec_output push:
if (currentSession.value && spec) {
  const su = specUsage.value
  currentSession.value.messages.push({
    message_id: crypto.randomUUID(),
    role: 'assistant',
    content: spec,
    message_type: 'spec_output',
    timestamp: new Date().toISOString(),
    input_tokens: su?.input_tokens ?? null,
    output_tokens: su?.output_tokens ?? null,
    cost_usd: su?.cost_usd ?? null,
  })
  specUsage.value = null  // clear after use
}
```

#### `frontend/src/components/chat/ChatMessage.vue`

Add token/cost display to the `spec_output` template block, matching the style used for `html_output`:

```html
<!-- Add after the timestamp line in the spec_output block -->
<div v-if="message.cost_usd != null" class="text-xs mt-1 font-mono text-cp-muted opacity-60 text-left">
  {{ message.input_tokens?.toLocaleString() }}&thinsp;in
  &middot; {{ message.output_tokens?.toLocaleString() }}&thinsp;out
  &middot; ${{ formatCost(message.cost_usd) }}
</div>
```

### Data Flow Summary

```
Phase 1 API call completes
  └─ usage_data = { input_tokens, output_tokens, cost_usd }
     ├─ Backend: persisted to MongoDB on spec_output message
     │    (NOT on the pre-text clarification message — avoids double-counting)
     ├─ WebSocket: sent via { type: "complete", usage: {...} }
     └─ Frontend store: captured in specUsage ref
           └─ Applied to spec_output message when onVisualizationReady fires

Phase 2 API call completes
  └─ usage_data = { input_tokens, output_tokens, cost_usd }
     ├─ Backend: persisted to MongoDB on html_output message
     ├─ WebSocket: sent via { type: "visualization_ready", usage: {...} }
     └─ Frontend store: applied to html_output message directly

Page Refresh / Resume
  └─ GET /api/visualizations/:vizId/chat returns session with messages from MongoDB
     ├─ spec_output message has input_tokens, output_tokens, cost_usd (after fix)
     └─ html_output message has input_tokens, output_tokens, cost_usd

totalSessionCost computation
  └─ Sums cost_usd across all messages in the session
     └─ Each LLM API call contributes exactly ONE cost entry (no duplication)
```

---

## 3. Streaming Modal Content Rendering

### Problem
When the user clicks "View" on either the spec-building or HTML-generation streaming progress bar, a full-screen modal opens showing the raw streamed text. Currently both modals render the content identically inside a `<pre>` tag with plain monospace text. This is suboptimal because:

1. **Spec modal:** The specification content is authored by the LLM in Markdown format (headings, lists, bold, code blocks, etc.), but the modal displays it as unformatted plain text. This makes it hard to scan and understand.
2. **HTML modal:** The generated HTML source code is displayed as plain text with no syntax highlighting, making it difficult to read and verify correctness during streaming.

The same issue applies to the **post-completion modals** rendered inside `ChatMessage.vue` (the "View" button on completed `spec_output` and `html_output` messages). These also display raw content in a `<pre>` tag.

### Required Behavior

#### 3.1 Spec Modal — Rendered Markdown

Both the live streaming modal (in `ChatWindow.vue`) and the completed-message modal (in `ChatMessage.vue`) must render the specification content as **formatted Markdown** instead of plain text:

- Use the existing `marked` library (already installed) to parse Markdown to HTML.
- Use the existing `dompurify` library (already installed) to sanitize the parsed HTML.
- The rendered Markdown should be displayed inside a styled `<div>` (not a `<pre>`) with appropriate prose/typography styles matching the chat message rendering.
- During live streaming, the Markdown should re-render on every chunk update so the user sees formatted content building up in real time.
- The modal header badge should change from "Plain text" to "Markdown".

#### 3.2 HTML Modal — Syntax-Highlighted Code

Both the live streaming modal (in `ChatWindow.vue`) and the completed-message modal (in `ChatMessage.vue`) must render the HTML source code with **syntax highlighting**:

- Install `highlight.js` as a dependency.
- Use highlight.js to apply syntax highlighting for HTML/XML content.
- Import only the HTML/XML language definition to minimize bundle size.
- Use a dark theme (e.g., `github-dark` or `atom-one-dark`) that matches the application's dark UI.
- During live streaming, the highlighted content should update on every chunk so the user sees colored syntax building up in real time.
- Display inside a `<pre><code>` block with the highlight.js classes applied.

### Affected Files

#### `frontend/package.json`

Add `highlight.js` dependency:

```json
"highlight.js": "^11.10.0"
```

#### `frontend/src/components/chat/ChatWindow.vue`

**Live streaming modal content area** — replace the single `<pre>` block with conditional rendering:

```html
<!-- BEFORE -->
<div ref="liveModalScrollEl" class="flex-1 overflow-auto">
  <pre class="p-5 text-xs font-mono text-cp-text/90 whitespace-pre-wrap break-all leading-relaxed min-h-full">{{ liveModalType === 'spec' ? chatStore.specStreamBuffer : chatStore.htmlStreamBuffer }}</pre>
</div>

<!-- AFTER -->
<div ref="liveModalScrollEl" class="flex-1 overflow-auto">
  <!-- Spec: rendered Markdown -->
  <div
    v-if="liveModalType === 'spec'"
    class="p-5 text-sm text-cp-text prose-chat break-words leading-relaxed min-h-full"
    v-html="renderedSpecStream"
  ></div>
  <!-- HTML: syntax-highlighted code -->
  <pre
    v-else
    class="p-5 text-xs font-mono leading-relaxed min-h-full"
  ><code class="language-html" v-html="highlightedHtmlStream"></code></pre>
</div>
```

Add computed properties in `<script setup>`:

```javascript
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js/lib/core'
import xml from 'highlight.js/lib/languages/xml'
import 'highlight.js/styles/github-dark.min.css'

hljs.registerLanguage('xml', xml)

const renderedSpecStream = computed(() => {
  const raw = chatStore.specStreamBuffer || ''
  if (!raw) return ''
  const html = marked.parse(raw)
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
})

const highlightedHtmlStream = computed(() => {
  const raw = chatStore.htmlStreamBuffer || ''
  if (!raw) return ''
  return hljs.highlight(raw, { language: 'xml' }).value
})
```

Also update the header badge text in the live modal:

```html
<!-- BEFORE -->
<!-- (no badge in live modal header — add one) -->

<!-- AFTER (add after the "Streaming…" / "Complete" span) -->
<span class="text-xs text-cp-muted px-2 py-0.5 rounded bg-cp-surface border border-cp-border/50">
  {{ liveModalType === 'spec' ? 'Markdown' : 'HTML' }}
</span>
```

#### `frontend/src/components/chat/ChatMessage.vue`

**Completed-message modal content area** — replace the single `<pre>` block with conditional rendering:

```html
<!-- BEFORE -->
<div class="flex-1 overflow-auto bg-cp-black rounded-b-xl">
  <pre class="h-full p-5 text-xs font-mono text-cp-text/90 whitespace-pre-wrap break-all leading-relaxed">{{ modalContent }}</pre>
</div>

<!-- AFTER -->
<div class="flex-1 overflow-auto bg-cp-black rounded-b-xl">
  <!-- Spec: rendered Markdown -->
  <div
    v-if="modalType === 'spec'"
    class="p-5 text-sm text-cp-text prose-chat break-words leading-relaxed"
    v-html="renderedModalContent"
  ></div>
  <!-- HTML: syntax-highlighted code -->
  <pre
    v-else
    class="h-full p-5 text-xs font-mono leading-relaxed"
  ><code class="language-html" v-html="highlightedModalContent"></code></pre>
</div>
```

Add computed properties and imports in `<script setup>`:

```javascript
import hljs from 'highlight.js/lib/core'
import xml from 'highlight.js/lib/languages/xml'
import 'highlight.js/styles/github-dark.min.css'

hljs.registerLanguage('xml', xml)

const renderedModalContent = computed(() => {
  const raw = props.message.content ?? ''
  if (!raw) return ''
  const html = marked.parse(raw)
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
})

const highlightedModalContent = computed(() => {
  const raw = props.message.content ?? ''
  if (!raw) return ''
  return hljs.highlight(raw, { language: 'xml' }).value
})
```

Update the modal header badge text:

```html
<!-- BEFORE -->
<span class="text-xs text-cp-muted px-2 py-0.5 rounded bg-cp-surface border border-cp-border/50">
  {{ modalType === 'spec' ? 'Plain text' : 'HTML' }}
</span>

<!-- AFTER -->
<span class="text-xs text-cp-muted px-2 py-0.5 rounded bg-cp-surface border border-cp-border/50">
  {{ modalType === 'spec' ? 'Markdown' : 'HTML' }}
</span>
```

### Visual Result

#### Spec Modal (before → after)

| Before | After |
|--------|-------|
| Plain monospace text with `#` symbols, `*` markers, etc. visible | Rendered headings, bold text, bullet lists, code blocks with proper formatting |

#### HTML Modal (before → after)

| Before | After |
|--------|-------|
| White monospace text, no color differentiation | Syntax-colored tags (`<div>` in one color), attributes in another, strings in another, matching the `github-dark` highlight.js theme |

---

## 4. Testing Notes

- **Cost rounding:** Verify that the header total cost badge and per-message cost labels all display 2 decimal places with the `$0.01` floor.
- **Spec progress bar after refresh:** Create a visualization, let it complete through both phases, then refresh the page. Both the spec and HTML progress bars should show token counts and cost.
- **No double-counting:** Confirm that `totalSessionCost` (summing all messages' `cost_usd`) matches the visualization's `total_cost_usd` stored on the backend, with no duplication from the pre-text clarification message.
- **Spec modal Markdown rendering:** Open the spec modal (both during streaming and after completion) and verify Markdown headings, lists, bold, and code blocks render correctly as formatted HTML.
- **HTML modal syntax highlighting:** Open the HTML modal (both during streaming and after completion) and verify HTML tags, attributes, and values are syntax-colored.
- **Streaming updates:** While the spec is streaming, the modal should show progressively rendered Markdown. While the HTML is streaming, the modal should show progressively syntax-highlighted code.
