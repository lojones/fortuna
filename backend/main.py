import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import settings
from app.db.init_db import init_db
from app.db.mongodb import get_database
from app.routers import auth, users, visualizations, chat
from app.services import visualization_service

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title="Fortuna API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(visualizations.router, prefix="/api/visualizations", tags=["visualizations"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/visualization/{slug}", response_class=HTMLResponse)
async def serve_published_visualization(slug: str):
    """Serve a published visualization as a full HTML page. No auth required."""
    db = get_database()
    viz = await visualization_service.get_published_by_slug(db, slug)
    if not viz or not viz.published_html:
        return HTMLResponse(
            content="<html><body><h1>404 — Visualization not found</h1><p>This visualization may have been unpublished or does not exist.</p></body></html>",
            status_code=404,
        )
    return HTMLResponse(content=viz.published_html)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
