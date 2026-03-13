# Branding Specification

## Version 1.0.0

---

## 1. Overview

This specification defines the branding and naming conventions for the application. The user-facing brand name is **Visualizr**. The internal code name is **Fortuna**. This document establishes rules for where each name appears and how to handle future brand changes without disrupting the codebase.

---

## 2. Naming Definitions

| Term | Value | Audience |
|------|-------|----------|
| **Brand Name** | Visualizr | External — all user-facing surfaces |
| **Internal Code Name** | Fortuna | Internal — code, repos, infra, developer docs |

### 2.1 Brand Name — `Visualizr`

The brand name is what users see. It appears in:

- Browser tab / page title
- Login and registration screens (logo, headings)
- App header / navigation bar
- Dashboard welcome messages
- Footer text and copyright notices
- Notification and toast messages
- Error pages and empty states
- Email communications (if applicable)
- `<meta>` tags (`og:title`, `og:site_name`, `description`)
- Favicon alt text
- README hero section (public-facing portion)
- Any marketing or onboarding copy

### 2.2 Internal Code Name — `Fortuna`

The internal code name is never exposed to end users. It appears in:

- Repository name (`fortuna`)
- Database name (`fortuna`)
- Python package/module names (`app/`, import paths)
- Docker service names and container names
- Environment variable prefixes (where already established)
- Internal developer documentation (`CLAUDE.md`, inline code comments)
- CI/CD pipeline identifiers
- Log prefixes and internal telemetry
- JWT issuer field (if set)
- Backend config class names (e.g., `Settings` in `config.py`)

---

## 3. Implementation Rules

### 3.1 Single Source of Truth

The brand name **must** be defined in exactly one location per layer so that a future rebrand requires minimal changes:

| Layer | Location | Current Value |
|-------|----------|---------------|
| Frontend | `frontend/src/App.vue` or a dedicated `brandConfig.js` constant | `"Visualizr"` |
| Backend | Not typically rendered to users; if needed, via `app/config.py` | `"Visualizr"` |
| HTML | `frontend/index.html` `<title>` tag | `Visualizr` |

All components that display the brand name **must** reference the single constant rather than hard-coding the string.

#### Recommended Frontend Constant

Create or update a brand config file:

**`frontend/src/config/brand.js`**

```javascript
export const BRAND_NAME = 'Visualizr'
export const BRAND_TAGLINE = 'Describe it. Visualize it.'
```

All Vue components reference `BRAND_NAME` instead of a literal string.

### 3.2 Hard-Coded String Audit

Any existing hard-coded reference to "Fortuna" in user-facing text must be replaced with the brand name constant. Specifically:

| File | What to Change |
|------|---------------|
| `frontend/index.html` | `<title>` tag: change to `Visualizr` |
| `frontend/src/components/common/AppHeader.vue` | App name in the header bar |
| `frontend/src/components/common/AppFooter.vue` | Footer brand / copyright text |
| `frontend/src/views/LoginView.vue` | Login heading and logo text |
| `frontend/src/views/RegisterView.vue` | Registration heading |
| `frontend/src/views/DashboardView.vue` | Welcome banner text (if it mentions the app name) |

### 3.3 What Must NOT Change

The following must remain as `fortuna` regardless of any brand change:

- Repository and directory names
- MongoDB database name (`fortuna`)
- Python module and package names
- Docker Compose service names
- Internal spec files and developer-only docs (e.g., `CLAUDE.md`)
- Environment variable names already using `fortuna` conventions
- Backend log identifiers

---

## 4. Visual Assets

### 4.1 Logo

- The logo should display the word **Visualizr** in a clean, modern sans-serif font.
- A stylized "V" mark may be used as a compact icon (favicon, mobile).
- No reference to "Fortuna" should appear in any visual asset delivered to users.

### 4.2 Favicon

- `frontend/public/favicon.ico` (and any SVG variant) should reflect the Visualizr brand.
- The `<link rel="icon">` in `index.html` points to the branded favicon.

### 4.3 Open Graph / Social Meta

```html
<meta property="og:title" content="Visualizr" />
<meta property="og:site_name" content="Visualizr" />
<meta property="og:description" content="Describe it. Visualize it." />
```

---

## 5. Future Brand Changes

When the brand name changes:

1. Update `BRAND_NAME` in `frontend/src/config/brand.js`.
2. Update `<title>` in `frontend/index.html`.
3. Update Open Graph meta tags in `frontend/index.html`.
4. Replace visual assets (logo, favicon).
5. **Do not** rename the repository, database, or any internal identifiers — the code name `fortuna` is permanent.

No other code changes should be necessary if the single-source-of-truth rule (§3.1) has been followed.

---

## 6. Acceptance Criteria

- [ ] All user-facing UI text displays **Visualizr**, never "Fortuna".
- [ ] A single `BRAND_NAME` constant exists in the frontend and is used by all components that render the app name.
- [ ] `<title>` tag reads "Visualizr".
- [ ] The internal code name "fortuna" is absent from any text, tooltip, heading, or label visible to end users.
- [ ] A future brand change can be accomplished by updating the constant, `<title>`, meta tags, and visual assets — no grep-and-replace across components.
