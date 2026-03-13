# SPEC6 — Application Deployment to Azure

## 1. Overview

Fortuna uses a split deployment model:

| Component | Azure Resource | Resource Name | Build Artifact | Registry |
|-----------|---------------|---------------|----------------|----------|
| Frontend (Vue 3 SPA) | Azure Static Web App | `fortuna-ui` | Static files (`dist/`) | N/A (deployed directly) |
| Backend (FastAPI) | Azure Container App | `fortuna-backend` | Docker image | GitHub Container Registry (`ghcr.io`) |

Both deployments are triggered automatically by GitHub Actions on push to the `master` branch.

---

## 2. Frontend — Azure Static Web App

### 2.1 Resource

- **Azure resource type:** Static Web App
- **Name:** `fortuna-ui`
- **Framework:** Vue 3 + Vite (detected automatically by Azure SWA)

### 2.2 Build

The frontend is a standard Vite project. The build step runs:

```bash
cd frontend
npm ci
npm run build
```

This produces a `frontend/dist/` directory containing the production SPA assets.

### 2.3 Routing

Azure Static Web Apps must serve `index.html` for all non-file routes so that Vue Router handles client-side navigation. This is configured via a `staticwebapp.config.json` in the `frontend/` directory:

```json
{
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/assets/*", "/favicon.ico"]
  }
}
```

### 2.4 Environment Variables

The following environment variables must be set in the Azure Static Web App configuration (Settings → Configuration → Application settings):

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `https://fortuna-backend.<region>.azurecontainerapps.io` |
| `VITE_WS_BASE_URL` | Backend WebSocket base URL | `wss://fortuna-backend.<region>.azurecontainerapps.io` |

> **Note:** Vite embeds `VITE_*` variables at build time, so these must be available during the GitHub Actions build step (set as repository secrets or workflow env vars), not as Azure runtime settings.

### 2.5 GitHub Actions Workflow

**Trigger:** Push to `master` branch, changes in `frontend/` path.

**File:** `.github/workflows/deploy-frontend.yml`

```yaml
name: Deploy Frontend to Azure Static Web App

on:
  push:
    branches:
      - master
    paths:
      - 'frontend/**'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Deploy to Azure Static Web App
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "frontend"
          output_location: "dist"
        env:
          VITE_API_BASE_URL: ${{ secrets.VITE_API_BASE_URL }}
          VITE_WS_BASE_URL: ${{ secrets.VITE_WS_BASE_URL }}
```

### 2.6 Required Secrets

| Secret | Source |
|--------|--------|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Azure Portal → Static Web App → Manage deployment token |
| `VITE_API_BASE_URL` | The public URL of the backend Container App |
| `VITE_WS_BASE_URL` | Same host as API base URL but with `wss://` scheme |

---

## 3. Backend — Azure Container App

### 3.1 Resource

- **Azure resource type:** Container App
- **Name:** `fortuna-backend`
- **Image source:** `ghcr.io/lojones/fortuna-backend:latest`
- **Ingress:** External, port 8000
- **Transport:** HTTP (with WebSocket support enabled)

### 3.2 Dockerfile

A `Dockerfile` in the repository root (or `backend/`) builds the FastAPI application:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.3 Environment Variables

The following must be configured as secrets/environment variables on the Azure Container App:

| Variable | Description |
|----------|-------------|
| `MONGODB_URI` | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | `fortuna` |
| `JWT_SECRET_KEY` | Random 256-bit hex secret |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_EXPIRY_MINUTES` | `480` |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `DEFAULT_ADMIN_USERNAME` | Seed admin username |
| `DEFAULT_ADMIN_EMAIL` | Seed admin email |
| `DEFAULT_ADMIN_PASSWORD` | Seed admin password |
| `FRONTEND_ORIGIN` | Public URL of `fortuna-ui` Static Web App |
| `LOG_LEVEL` | `INFO` (or `DEBUG`) |

Sensitive values (`MONGODB_URI`, `JWT_SECRET_KEY`, `ANTHROPIC_API_KEY`, `DEFAULT_ADMIN_PASSWORD`) should be stored as Azure Container App secrets, not plain environment variables.

### 3.4 GitHub Actions Workflow

**Trigger:** Push to `master` branch, changes in `backend/` path.

The workflow builds a Docker image, pushes it to GitHub Container Registry (`ghcr.io`), then deploys the new image to the Azure Container App.

**File:** `.github/workflows/deploy-backend.yml`

```yaml
name: Deploy Backend to Azure Container App

on:
  push:
    branches:
      - master
    paths:
      - 'backend/**'
      - 'Dockerfile'

env:
  IMAGE_NAME: ghcr.io/lojones/fortuna-backend

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: |
            ${{ env.IMAGE_NAME }}:latest
            ${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Log in to Azure
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy to Azure Container App
        uses: azure/container-apps-deploy-action@v1
        with:
          containerAppName: fortuna-backend
          resourceGroup: ${{ secrets.AZURE_RESOURCE_GROUP }}
          imageToDeploy: ${{ env.IMAGE_NAME }}:${{ github.sha }}
```

### 3.5 Required Secrets

| Secret | Source |
|--------|--------|
| `AZURE_CREDENTIALS` | Azure service principal JSON (`az ad sp create-for-rbac`) |
| `AZURE_RESOURCE_GROUP` | Name of the Azure resource group containing `fortuna-backend` |

> `GITHUB_TOKEN` is provided automatically by GitHub Actions and has `packages:write` permission for pushing to `ghcr.io`.

### 3.6 Container App Configuration

The Azure Container App must be configured with:

- **Ingress:** External, target port `8000`
- **Transport:** HTTP (Azure Container Apps supports WebSocket over HTTP ingress natively)
- **Min replicas:** 1 (to avoid cold starts during WebSocket connections)
- **Max replicas:** Adjust based on load (WebSocket connections are long-lived, so scale conservatively)
- **Health probe:** HTTP GET `/api/health` on port 8000

---

## 4. Image Tagging Strategy

Each backend build produces two tags:

| Tag | Purpose |
|-----|---------|
| `latest` | Convenience tag, always points to the most recent build |
| `<commit-sha>` | Immutable tag tied to the exact source commit for traceability and rollback |

The Container App deployment uses the SHA tag to ensure deterministic deployments. Rollbacks can target any previously pushed SHA tag.

---

## 5. CORS Configuration

The backend `FRONTEND_ORIGIN` environment variable must be set to the production URL of the Static Web App (e.g., `https://fortuna-ui.azurestaticapps.net` or a custom domain). This value is used by the FastAPI CORS middleware to allow cross-origin requests from the frontend.

---

## 6. DNS & Custom Domains (Optional)

Both Azure Static Web Apps and Azure Container Apps support custom domain binding with managed TLS certificates. If custom domains are used:

1. Add a CNAME or A record pointing to the Azure resource
2. Bind the domain in the Azure portal
3. Update `FRONTEND_ORIGIN` on the backend to match the custom frontend domain
4. Update `VITE_API_BASE_URL` / `VITE_WS_BASE_URL` to match the custom backend domain

---

## 7. Deployment Flow Summary

```
                        push to master
                              │
                 ┌────────────┴────────────┐
                 │                         │
          frontend/** changed?      backend/** changed?
                 │                         │
                 ▼                         ▼
          npm ci && build         docker build & push
          (Vite → dist/)         (ghcr.io/lojones/
                 │                 fortuna-backend:sha)
                 ▼                         │
        Azure Static Web App               ▼
          (fortuna-ui)            Azure Container App
                                  (fortuna-backend)
```

Both pipelines are independent — a frontend-only change does not rebuild or redeploy the backend, and vice versa.
