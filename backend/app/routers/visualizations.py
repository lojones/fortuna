import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.mongodb import get_database
from app.models.user import UserInDB
from app.models.visualization import VisualizationCreate, VisualizationPublic
from app.services.auth_service import get_current_user
from app.services import visualization_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=List[VisualizationPublic])
async def get_my_visualizations(current_user: UserInDB = Depends(get_current_user)):
    logger.debug(f"Fetching all visualizations for user='{current_user.username}'")
    db = get_database()
    vizs = await visualization_service.get_visualizations_by_owner(db, current_user.id)
    logger.debug(f"Found {len(vizs)} visualization(s) for user='{current_user.username}'")
    return vizs


@router.get("/recent", response_model=Optional[VisualizationPublic])
async def get_recent_visualization(current_user: UserInDB = Depends(get_current_user)):
    logger.debug(f"Fetching most recent visualization for user='{current_user.username}'")
    db = get_database()
    viz = await visualization_service.get_most_recent_visualization(db, current_user.id)
    if viz:
        logger.debug(f"Most recent viz for '{current_user.username}': id={viz.id} title='{viz.title}'")
    else:
        logger.debug(f"No visualizations found for user='{current_user.username}'")
    return viz


@router.post("", response_model=VisualizationPublic, status_code=status.HTTP_201_CREATED)
async def create_visualization(
    body: VisualizationCreate, current_user: UserInDB = Depends(get_current_user)
):
    logger.info(f"Creating visualization title='{body.title}' for user='{current_user.username}'")
    db = get_database()
    viz = await visualization_service.create_visualization(
        db, current_user.id, body.title, body.description
    )
    logger.info(f"Visualization created: id={viz.id} title='{viz.title}' chat_session_id={viz.chat_session_id}")
    return viz


@router.get("/public/{slug}")
async def get_published_visualization(slug: str):
    """Public endpoint — no auth required. Returns published visualization by slug."""
    logger.debug(f"Public fetch for slug='{slug}'")
    db = get_database()
    viz = await visualization_service.get_published_by_slug(db, slug)
    if not viz or not viz.published_html:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published visualization not found",
        )
    # Look up owner username
    owner_doc = await db.users.find_one({"_id": __import__("bson").ObjectId(viz.owner_id)})
    owner_username = owner_doc["username"] if owner_doc else "unknown"
    return {
        "slug": viz.published_slug,
        "title": viz.title,
        "html_content": viz.published_html,
        "published_at": viz.published_at,
        "owner_username": owner_username,
    }


@router.get("/{viz_id}", response_model=VisualizationPublic)
async def get_visualization(viz_id: str, current_user: UserInDB = Depends(get_current_user)):
    logger.debug(f"Fetching visualization id={viz_id} for user='{current_user.username}'")
    db = get_database()
    viz = await visualization_service.get_visualization_by_id(db, viz_id)
    if not viz:
        logger.warning(f"Visualization id={viz_id} not found (requested by '{current_user.username}')")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visualization not found"
        )
    if viz.owner_id != current_user.id:
        logger.warning(f"Access denied: user='{current_user.username}' attempted to access viz id={viz_id} owned by id={viz.owner_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return viz


@router.get("/{viz_id}/chat")
async def get_visualization_chat(
    viz_id: str, current_user: UserInDB = Depends(get_current_user)
):
    logger.debug(f"Fetching chat session for viz id={viz_id}, user='{current_user.username}'")
    db = get_database()
    viz = await visualization_service.get_visualization_by_id(db, viz_id)
    if not viz:
        logger.warning(f"Chat fetch failed: viz id={viz_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visualization not found"
        )
    if viz.owner_id != current_user.id:
        logger.warning(f"Chat fetch denied: user='{current_user.username}' does not own viz id={viz_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    session = await visualization_service.get_chat_session(db, viz.chat_session_id)
    logger.debug(f"Returning chat session id={viz.chat_session_id} with {len(session.messages) if session else 0} message(s)")
    return session


@router.post("/{viz_id}/publish", response_model=VisualizationPublic)
async def publish_visualization(
    viz_id: str, current_user: UserInDB = Depends(get_current_user)
):
    logger.info(f"Publish requested for viz id={viz_id} by user='{current_user.username}'")
    db = get_database()
    viz = await visualization_service.get_visualization_by_id(db, viz_id)
    if not viz:
        logger.warning(f"Publish failed: viz id={viz_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visualization not found"
        )
    if viz.owner_id != current_user.id:
        logger.warning(f"Publish denied: user='{current_user.username}' does not own viz id={viz_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can publish"
        )

    updated = await visualization_service.publish_visualization(
        db, viz_id, current_user.id
    )
    logger.info(f"Visualization id={viz_id} published as version {updated.latest_published_version} by '{current_user.username}'")
    return updated


@router.post("/{viz_id}/publish-version/{version_number}", response_model=VisualizationPublic)
async def publish_version(
    viz_id: str, version_number: int, current_user: UserInDB = Depends(get_current_user)
):
    """Publish a specific existing version as the live public artifact."""
    logger.info(f"Publish version {version_number} requested for viz id={viz_id} by user='{current_user.username}'")
    db = get_database()
    updated = await visualization_service.publish_version(
        db, viz_id, version_number, current_user.id
    )
    logger.info(f"Version {version_number} of viz id={viz_id} published by '{current_user.username}'")
    return updated


@router.post("/{viz_id}/unpublish", response_model=VisualizationPublic)
async def unpublish_visualization(
    viz_id: str, current_user: UserInDB = Depends(get_current_user)
):
    """Remove the public URL and take the visualization offline."""
    logger.info(f"Unpublish requested for viz id={viz_id} by user='{current_user.username}'")
    db = get_database()
    updated = await visualization_service.unpublish_visualization(
        db, viz_id, current_user.id
    )
    logger.info(f"Visualization id={viz_id} unpublished by '{current_user.username}'")
    return updated


@router.get("/{viz_id}/versions/{version_number}")
async def get_version(
    viz_id: str, version_number: int, current_user: UserInDB = Depends(get_current_user)
):
    logger.debug(f"Fetching version {version_number} of viz id={viz_id} for user='{current_user.username}'")
    db = get_database()
    viz = await visualization_service.get_visualization_by_id(db, viz_id)
    if not viz:
        logger.warning(f"Version fetch failed: viz id={viz_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visualization not found"
        )
    if viz.owner_id != current_user.id:
        logger.warning(f"Version fetch denied: user='{current_user.username}' does not own viz id={viz_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    for v in viz.published_versions:
        if v.version_number == version_number:
            logger.debug(f"Returning version {version_number} of viz id={viz_id}")
            return {
                "version_number": v.version_number,
                "html_content": v.html_content,
                "published_at": v.published_at,
            }

    logger.warning(f"Version {version_number} not found for viz id={viz_id}")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Version not found"
    )


@router.delete("/{viz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_visualization(
    viz_id: str, current_user: UserInDB = Depends(get_current_user)
):
    logger.info(f"Delete requested for viz id={viz_id} by user='{current_user.username}'")
    db = get_database()
    await visualization_service.delete_visualization(db, viz_id, current_user.id)
    logger.info(f"Visualization id={viz_id} deleted by '{current_user.username}'")
