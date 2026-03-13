# SPEC4: Publishing Visualizations

## Overview

This spec defines how visualizations are published to publicly accessible URLs. A published visualization is hosted at a deterministic, human-readable URL and is viewable by anyone — no authentication required. Each visualization can have at most one published artifact live at a time, and the owner controls publishing, unpublishing, and which version is live.

---

## 1. Core Rules

1. **One published artifact per visualization.** A visualization may have many versioned snapshots in `published_versions`, but only **one** can be the actively published (live) artifact at any time.
2. **Public access.** Published visualizations are served at a public URL with no authentication required.
3. **Owner-only control.** Only the visualization's owner can publish, unpublish, or change which version is live.
4. **Any version is publishable.** The owner can choose to publish the current draft **or** any previously saved version from `published_versions` as the live artifact.

---

## 2. Published URL Scheme

Published visualizations are hosted at:

```
https://(domain)/visualization/(published_slug)
```

For example: `https://fortuna.app/visualization/quarterly-revenue-chart`

### 2.1 Slug Generation

When a visualization is first published, a URL-friendly **slug** is generated from the visualization's `title`:

1. Convert to lowercase.
2. Replace spaces and non-alphanumeric characters (except hyphens) with hyphens.
3. Collapse consecutive hyphens into a single hyphen.
4. Trim leading/trailing hyphens.
5. Truncate to a maximum of 80 characters (at a word boundary if possible).

**Examples:**
| Title | Generated Slug |
|---|---|
| `Quarterly Revenue Chart` | `quarterly-revenue-chart` |
| `My Analysis (v2)` | `my-analysis-v2` |
| `Hello   World!!!` | `hello-world` |

### 2.2 Slug Uniqueness

Slugs must be **globally unique** across all visualizations in the application, regardless of owner. If a generated slug collides with an existing one:

1. Append `-2` to the slug.
2. If `-2` also collides, try `-3`, `-4`, etc.
3. Continue until a unique slug is found.

**Example:** If `quarterly-revenue-chart` is already taken, the new slug becomes `quarterly-revenue-chart-2`.

### 2.3 Slug Persistence

Once a slug is assigned to a visualization, it does **not** change — even if the visualization title is later edited. The slug is a stable identifier. A slug is only freed when the visualization is deleted or unpublished.

---

## 3. Database Changes

### 3.1 `visualizations` Collection — New Fields

Add the following fields to the visualization document:

```json
{
  "published_slug": "string | null",
  "published_html": "string | null",
  "published_version_number": "integer | null",
  "published_at": "datetime | null"
}
```

| Field | Description |
|---|---|
| `published_slug` | The URL-friendly slug for the public URL. `null` when not published. |
| `published_html` | The HTML content currently being served at the public URL. `null` when not published. |
| `published_version_number` | The version number from `published_versions` that is currently live, or `null` if the live content was published directly from the current draft (before it was added to `published_versions`). |
| `published_at` | Timestamp of when the current live artifact was published. `null` when not published. |

### 3.2 New Index

Create a **unique sparse index** on `published_slug`:

```python
await db.visualizations.create_index("published_slug", unique=True, sparse=True)
```

This enforces slug uniqueness at the database level while allowing multiple documents to have `published_slug: null`.

---

## 4. Backend Changes

### 4.1 Model Changes (`app/models/visualization.py`)

Add fields to `VisualizationInDB` and `VisualizationPublic`:

```python
class VisualizationInDB(VisualizationBase):
    # ... existing fields ...
    published_slug: Optional[str] = None
    published_html: Optional[str] = None
    published_version_number: Optional[int] = None
    published_at: Optional[datetime] = None
```

### 4.2 Service Changes (`app/services/visualization_service.py`)

#### `generate_slug(db, title: str) -> str`

```
FUNCTION generate_slug(db, title: str) -> str:
    base_slug = slugify(title)  # Apply rules from §2.1
    IF base_slug is empty:
        base_slug = "visualization"
    
    candidate = base_slug
    suffix = 2
    WHILE await db.visualizations.find_one({"published_slug": candidate}):
        candidate = f"{base_slug}-{suffix}"
        suffix += 1
    RETURN candidate
```

#### Updated `publish_visualization`

The existing `publish_visualization` function is modified. When publishing, the system:

1. Saves the draft HTML into `published_versions` as a new version (existing behavior).
2. Generates a slug if the visualization doesn't already have one.
3. Sets `published_html` to the version's HTML content.
4. Sets `published_version_number` to the new version number.
5. Sets `published_at` to the current time.

```
FUNCTION publish_visualization(db, viz_id, publisher_id) -> VisualizationInDB:
    # ... existing version creation logic ...
    
    # Generate slug if first-time publish
    slug = doc.get("published_slug")
    IF slug is None:
        slug = await generate_slug(db, doc["title"])
    
    # Update document with live published state
    result = await db.visualizations.find_one_and_update(
        {"_id": ObjectId(viz_id)},
        {"$push": {"published_versions": new_version},
         "$set": {
             "latest_published_version": version_number,
             "status": "published",
             "published_slug": slug,
             "published_html": html_content,
             "published_version_number": version_number,
             "published_at": now,
             "updated_at": now,
         }},
        return_document=True
    )
    RETURN _viz_from_doc(result)
```

#### New: `publish_version(db, viz_id, version_number, publisher_id) -> VisualizationInDB`

Allows the owner to set any existing version from `published_versions` as the live published artifact.

```
FUNCTION publish_version(db, viz_id, version_number, publisher_id) -> VisualizationInDB:
    doc = await db.visualizations.find_one({"_id": ObjectId(viz_id)})
    IF not doc:
        RAISE 404
    IF str(doc["owner_id"]) != publisher_id:
        RAISE 403 "Only the owner can publish"
    
    # Find the requested version
    version = None
    FOR v IN doc.get("published_versions", []):
        IF v["version_number"] == version_number:
            version = v
            BREAK
    IF version is None:
        RAISE 404 "Version not found"
    
    # Generate slug if first-time publish
    slug = doc.get("published_slug")
    IF slug is None:
        slug = await generate_slug(db, doc["title"])
    
    now = datetime.now(timezone.utc)
    result = await db.visualizations.find_one_and_update(
        {"_id": ObjectId(viz_id)},
        {"$set": {
            "published_slug": slug,
            "published_html": version["html_content"],
            "published_version_number": version_number,
            "published_at": now,
            "status": "published",
            "updated_at": now,
        }},
        return_document=True
    )
    RETURN _viz_from_doc(result)
```

#### New: `unpublish_visualization(db, viz_id, owner_id) -> VisualizationInDB`

```
FUNCTION unpublish_visualization(db, viz_id, owner_id) -> VisualizationInDB:
    doc = await db.visualizations.find_one({"_id": ObjectId(viz_id)})
    IF not doc:
        RAISE 404
    IF str(doc["owner_id"]) != owner_id:
        RAISE 403 "Only the owner can unpublish"
    IF doc.get("published_slug") is None:
        RAISE 400 "Visualization is not published"
    
    now = datetime.now(timezone.utc)
    result = await db.visualizations.find_one_and_update(
        {"_id": ObjectId(viz_id)},
        {"$set": {
            "published_slug": None,
            "published_html": None,
            "published_version_number": None,
            "published_at": None,
            "status": "draft",
            "updated_at": now,
        }},
        return_document=True
    )
    RETURN _viz_from_doc(result)
```

#### Updated `delete_visualization`

When a visualization is deleted, its slug is freed automatically (the document is removed).

### 4.3 Router Changes (`app/routers/visualizations.py`)

#### New Endpoints

```
POST /api/visualizations/{viz_id}/publish-version/{version_number}
    Auth: Required (owner only)
    Logic:
        1. Verify ownership
        2. Call visualization_service.publish_version(db, viz_id, version_number, current_user.id)
    Response 200: VisualizationPublic
    Response 404: "Version not found"
    Response 403: "Only the owner can publish"

POST /api/visualizations/{viz_id}/unpublish
    Auth: Required (owner only)
    Logic:
        1. Verify ownership
        2. Call visualization_service.unpublish_visualization(db, viz_id, current_user.id)
    Response 200: VisualizationPublic
    Response 400: "Visualization is not published"
    Response 403: "Only the owner can unpublish"
```

#### New Public Endpoint (no auth)

```
GET /api/visualizations/public/{slug}
    Auth: NONE (publicly accessible)
    Logic:
        1. Look up visualization by published_slug
        2. If not found or published_html is null, return 404
        3. Return the published HTML content
    Response 200: { slug: str, title: str, html_content: str, published_at: datetime, owner_username: str }
    Response 404: "Published visualization not found"
```

> **Note:** This endpoint must be defined **before** the `/{viz_id}` route in the router to avoid the path parameter capturing `"public"` as a `viz_id`.

### 4.4 Main App Route (`main.py`)

Add a catch-all or explicit route for serving published visualizations as full HTML pages:

```
GET /visualization/{slug}
    Auth: NONE
    Logic:
        1. Query db.visualizations.find_one({"published_slug": slug})
        2. If not found or published_html is null, return 404 HTML page
        3. Return published_html as an HTMLResponse (content_type: text/html)
    Response 200: Full HTML document (text/html)
    Response 404: Simple HTML error page
```

This route is mounted directly on the FastAPI app (not under `/api`) so that the URL is clean:
```python
@app.get("/visualization/{slug}")
async def serve_published_visualization(slug: str):
    ...
```

---

## 5. Frontend Changes

### 5.1 VisualizationView.vue

#### Publish Action Updates

The existing `PublishButton` behavior is extended. After a successful publish, show the published URL in a toast or inline banner so the user can copy it.

#### Unpublish Button

Add an **Unpublish** button that appears when the visualization has a `published_slug`. Clicking it:
1. Shows a confirmation dialog: "This will remove the public URL. Unpublish?"
2. On confirm, calls `POST /api/visualizations/{viz_id}/unpublish`.
3. Updates the local state.

#### Publish Specific Version

In the **Version History Sidebar**, each version entry gets a **"Publish this version"** action (in addition to the existing "Restore as Draft"). Clicking it:
1. Shows confirmation: "Publish Version {n} as the live visualization?"
2. Calls `POST /api/visualizations/{viz_id}/publish-version/{version_number}`.
3. Updates the local state and shows the public URL.

#### Published URL Display

When a visualization is published (`published_slug` is not null), show the public URL prominently in the header bar:
- Display as a clickable link that opens in a new tab.
- Include a "Copy URL" button next to it.

### 5.2 Visualization Service (`services/visualizationService.js`)

Add new API methods:

```javascript
publishVersion(vizId, versionNumber) {
    return api.post(`/api/visualizations/${vizId}/publish-version/${versionNumber}`)
},

unpublish(vizId) {
    return api.post(`/api/visualizations/${vizId}/unpublish`)
},

getPublished(slug) {
    return api.get(`/api/visualizations/public/${slug}`)
},
```

### 5.3 Visualization Store (`stores/visualization.js`)

Add new actions:

```javascript
async function publishVersion(vizId, versionNumber) {
    isLoading.value = true
    error.value = null
    try {
        const response = await visualizationService.publishVersion(vizId, versionNumber)
        currentVisualization.value = response.data
        return response.data
    } catch (err) {
        error.value = err.response?.data?.detail || 'Failed to publish version'
        throw err
    } finally {
        isLoading.value = false
    }
}

async function unpublishVisualization(vizId) {
    isLoading.value = true
    error.value = null
    try {
        const response = await visualizationService.unpublish(vizId)
        currentVisualization.value = response.data
        return response.data
    } catch (err) {
        error.value = err.response?.data?.detail || 'Failed to unpublish'
        throw err
    } finally {
        isLoading.value = false
    }
}
```

### 5.4 Router (`router/index.js`)

Add a new **public** route (no auth required) for viewing published visualizations in the Vue app. This route renders the visualization in a full-screen iframe without the app chrome:

```javascript
{
    path: '/visualization/:slug',
    name: 'PublishedVisualization',
    component: () => import('../views/PublishedVisualizationView.vue'),
    meta: { public: true },  // No auth required
}
```

> **Note:** This route conflicts with the existing `/visualization/:vizId` route. To resolve this, rename the existing owner-facing route to `/my/visualization/:vizId` or use a distinguishing prefix. Alternatively, the public route can be served entirely by the FastAPI HTML endpoint (§4.4), bypassing the Vue router entirely. **Recommended approach:** Serve published visualizations directly from FastAPI as full HTML responses at `/visualization/{slug}`, and rename the existing Vue route to `/editor/:vizId` or keep it as-is if the slug is always textual and `vizId` is always a hex ObjectId (they won't collide).

### 5.5 New View: `PublishedVisualizationView.vue` (optional)

If the Vue router approach is used instead of the FastAPI direct-serve approach, create a minimal view:

```
Template:
    - Full-screen iframe with no app header/footer
    - Fetches HTML via GET /api/visualizations/public/{slug}
    - Shows a small "Made with Fortuna" watermark in the corner (optional)
    - 404 state if slug not found
```

**Recommended:** Use the FastAPI direct HTML response (§4.4) instead of this view, since published visualizations are standalone HTML documents and benefit from being served without the Vue app shell.

---

## 6. Dashboard Changes

### 6.1 VisualizationCard.vue

Update each visualization card on the dashboard to show:
- A **"Published"** badge with a link icon when `published_slug` is not null.
- Clicking the badge opens the public URL in a new tab.

---

## 7. Database Initialization (`app/db/init_db.py`)

Add the sparse unique index on startup:

```python
async def init_db():
    # ... existing admin seed logic ...
    
    # Ensure indexes
    await db.visualizations.create_index("published_slug", unique=True, sparse=True)
```

---

## 8. Security Considerations

1. **No auth on public endpoints.** The `GET /visualization/{slug}` and `GET /api/visualizations/public/{slug}` endpoints must not require authentication.
2. **Ownership enforcement.** All publish/unpublish mutations verify `owner_id == current_user.id` in the service layer.
3. **Sandboxed rendering.** Published HTML is served as a complete HTML document. If served within an iframe on the Fortuna domain, use appropriate `sandbox` attributes. If served as a standalone page via FastAPI `HTMLResponse`, the content runs in its own browsing context with no access to the Fortuna app's cookies or localStorage.
4. **Slug injection.** Slugs are generated server-side from sanitized titles. The slug generation function must not allow path traversal characters (`/`, `..`, etc.).

---

## 9. Summary of New API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/visualizations/{viz_id}/publish-version/{version_number}` | Owner | Publish a specific version as the live artifact |
| `POST` | `/api/visualizations/{viz_id}/unpublish` | Owner | Remove the public URL and take the visualization offline |
| `GET` | `/api/visualizations/public/{slug}` | None | Fetch published visualization metadata + HTML by slug |
| `GET` | `/visualization/{slug}` | None | Serve published HTML directly as a web page |
