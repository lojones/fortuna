import logging
import re
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.visualization import VisualizationInDB, PublishedVersion, SpecVersion
from app.models.chat import ChatMessage, ChatSessionInDB

logger = logging.getLogger(__name__)


def _viz_from_doc(doc: dict) -> VisualizationInDB:
    published = []
    for pv in doc.get("published_versions", []):
        published.append(
            PublishedVersion(
                version_number=pv["version_number"],
                html_content=pv["html_content"],
                spec_version=pv.get("spec_version"),
                published_at=pv["published_at"],
                published_by=str(pv["published_by"]),
            )
        )
    spec_versions = []
    for sv in doc.get("spec_versions", []):
        spec_versions.append(
            SpecVersion(
                version_number=sv["version_number"],
                spec_text=sv["spec_text"],
                created_at=sv["created_at"],
            )
        )
    return VisualizationInDB(
        id=str(doc["_id"]),
        owner_id=str(doc["owner_id"]),
        title=doc["title"],
        description=doc.get("description"),
        status=doc["status"],
        current_draft_html=doc.get("current_draft_html"),
        current_draft_spec=doc.get("current_draft_spec"),
        spec_versions=spec_versions,
        latest_spec_version=doc.get("latest_spec_version"),
        published_versions=published,
        latest_published_version=doc.get("latest_published_version"),
        published_slug=doc.get("published_slug"),
        published_html=doc.get("published_html"),
        published_version_number=doc.get("published_version_number"),
        published_at=doc.get("published_at"),
        chat_session_id=str(doc["chat_session_id"]),
        total_cost_usd=doc.get("total_cost_usd", 0.0),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _session_from_doc(doc: dict) -> ChatSessionInDB:
    messages = []
    for m in doc.get("messages", []):
        messages.append(
            ChatMessage(
                message_id=m["message_id"],
                role=m["role"],
                content=m["content"],
                message_type=m["message_type"],
                timestamp=m["timestamp"],
                input_tokens=m.get("input_tokens"),
                output_tokens=m.get("output_tokens"),
                cost_usd=m.get("cost_usd"),
            )
        )
    return ChatSessionInDB(
        id=str(doc["_id"]),
        visualization_id=str(doc["visualization_id"]),
        owner_id=str(doc["owner_id"]),
        messages=messages,
        llm_state=doc["llm_state"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


async def create_visualization(
    db: AsyncIOMotorDatabase, owner_id: str, title: str, description: Optional[str] = None
) -> VisualizationInDB:
    logger.info(f"Creating visualization: title='{title}', owner_id={owner_id}")
    now = datetime.now(timezone.utc)

    # Create empty chat session first
    session_doc = {
        "visualization_id": None,  # will be updated
        "owner_id": ObjectId(owner_id),
        "messages": [],
        "llm_state": "clarifying",
        "created_at": now,
        "updated_at": now,
    }
    session_result = await db.chat_sessions.insert_one(session_doc)
    session_id = session_result.inserted_id
    logger.debug(f"Chat session created: id={session_id}")

    # Create visualization
    viz_doc = {
        "owner_id": ObjectId(owner_id),
        "title": title,
        "description": description,
        "status": "draft",
        "current_draft_html": None,
        "current_draft_spec": None,
        "spec_versions": [],
        "latest_spec_version": None,
        "published_versions": [],
        "latest_published_version": None,
        "chat_session_id": session_id,
        "created_at": now,
        "updated_at": now,
    }
    viz_result = await db.visualizations.insert_one(viz_doc)
    viz_id = viz_result.inserted_id
    logger.debug(f"Visualization document created: id={viz_id}")

    # Update session with visualization_id
    await db.chat_sessions.update_one(
        {"_id": session_id}, {"$set": {"visualization_id": viz_id}}
    )

    logger.info(f"Visualization created: id={viz_id}, session_id={session_id}, title='{title}'")
    viz_doc["_id"] = viz_id
    return _viz_from_doc(viz_doc)


async def get_visualizations_by_owner(
    db: AsyncIOMotorDatabase, owner_id: str
) -> List[VisualizationInDB]:
    vizs = []
    async for doc in db.visualizations.find({"owner_id": ObjectId(owner_id)}).sort(
        "updated_at", -1
    ):
        vizs.append(_viz_from_doc(doc))
    return vizs


async def get_visualization_by_id(
    db: AsyncIOMotorDatabase, viz_id: str
) -> Optional[VisualizationInDB]:
    doc = await db.visualizations.find_one({"_id": ObjectId(viz_id)})
    if doc:
        return _viz_from_doc(doc)
    return None


async def get_most_recent_visualization(
    db: AsyncIOMotorDatabase, owner_id: str
) -> Optional[VisualizationInDB]:
    doc = await db.visualizations.find_one(
        {"owner_id": ObjectId(owner_id)}, sort=[("updated_at", -1)]
    )
    if doc:
        return _viz_from_doc(doc)
    return None


async def update_draft_html(
    db: AsyncIOMotorDatabase, viz_id: str, html_content: str
) -> VisualizationInDB:
    now = datetime.now(timezone.utc)
    result = await db.visualizations.find_one_and_update(
        {"_id": ObjectId(viz_id)},
        {"$set": {"current_draft_html": html_content, "updated_at": now}},
        return_document=True,
    )
    return _viz_from_doc(result)


async def update_draft_spec(
    db: AsyncIOMotorDatabase, viz_id: str, spec_text: str
) -> VisualizationInDB:
    """Store a new spec version and update current_draft_spec."""
    logger.info(f"Versioning spec for viz_id={viz_id} ({len(spec_text)} chars)")
    now = datetime.now(timezone.utc)
    doc = await db.visualizations.find_one({"_id": ObjectId(viz_id)})
    version_number = len(doc.get("spec_versions", [])) + 1
    new_spec_version = {
        "version_number": version_number,
        "spec_text": spec_text,
        "created_at": now,
    }
    result = await db.visualizations.find_one_and_update(
        {"_id": ObjectId(viz_id)},
        {
            "$push": {"spec_versions": new_spec_version},
            "$set": {
                "current_draft_spec": spec_text,
                "latest_spec_version": version_number,
                "updated_at": now,
            },
        },
        return_document=True,
    )
    logger.info(f"Spec versioned as v{version_number} for viz_id={viz_id}")
    return _viz_from_doc(result)


async def publish_visualization(
    db: AsyncIOMotorDatabase, viz_id: str, publisher_id: str
) -> VisualizationInDB:
    logger.info(f"Publishing visualization id={viz_id} by publisher_id={publisher_id}")
    doc = await db.visualizations.find_one({"_id": ObjectId(viz_id)})
    if not doc:
        logger.warning(f"publish_visualization: viz_id={viz_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visualization not found"
        )

    if not doc.get("current_draft_html"):
        logger.warning(f"publish_visualization: viz_id={viz_id} has no draft HTML")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No draft content to publish",
        )

    version_number = len(doc.get("published_versions", [])) + 1
    now = datetime.now(timezone.utc)
    draft_size = len(doc["current_draft_html"])
    logger.debug(f"Publishing viz_id={viz_id} as version {version_number}, draft size={draft_size} chars")

    new_version = {
        "version_number": version_number,
        "html_content": doc["current_draft_html"],
        "spec_version": doc.get("latest_spec_version"),
        "published_at": now,
        "published_by": ObjectId(publisher_id),
    }

    # Generate slug if first-time publish
    slug = doc.get("published_slug")
    if slug is None:
        slug = await generate_slug(db, doc["title"])

    result = await db.visualizations.find_one_and_update(
        {"_id": ObjectId(viz_id)},
        {
            "$push": {"published_versions": new_version},
            "$set": {
                "latest_published_version": version_number,
                "status": "published",
                "published_slug": slug,
                "published_html": doc["current_draft_html"],
                "published_version_number": version_number,
                "published_at": now,
                "updated_at": now,
            },
        },
        return_document=True,
    )
    logger.info(f"Visualization id={viz_id} published as version {version_number}")
    return _viz_from_doc(result)


def _slugify(title: str) -> str:
    """Convert a title to a URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\-]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    # Truncate to 80 chars at a word boundary if possible
    if len(slug) > 80:
        truncated = slug[:80]
        last_hyphen = truncated.rfind("-")
        if last_hyphen > 40:
            truncated = truncated[:last_hyphen]
        slug = truncated.rstrip("-")
    return slug or "visualization"


async def generate_slug(db: AsyncIOMotorDatabase, title: str) -> str:
    """Generate a unique slug from a title, appending -2, -3, etc. if needed."""
    base_slug = _slugify(title)
    candidate = base_slug
    suffix = 2
    while await db.visualizations.find_one({"published_slug": candidate}):
        candidate = f"{base_slug}-{suffix}"
        suffix += 1
    return candidate


async def publish_version(
    db: AsyncIOMotorDatabase, viz_id: str, version_number: int, publisher_id: str
) -> VisualizationInDB:
    """Publish a specific existing version as the live artifact."""
    logger.info(f"Publishing version {version_number} of viz_id={viz_id} by publisher_id={publisher_id}")
    doc = await db.visualizations.find_one({"_id": ObjectId(viz_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visualization not found")
    if str(doc["owner_id"]) != publisher_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can publish")

    version = None
    for v in doc.get("published_versions", []):
        if v["version_number"] == version_number:
            version = v
            break
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    slug = doc.get("published_slug")
    if slug is None:
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
        return_document=True,
    )
    logger.info(f"Version {version_number} of viz_id={viz_id} published at slug='{slug}'")
    return _viz_from_doc(result)


async def unpublish_visualization(
    db: AsyncIOMotorDatabase, viz_id: str, owner_id: str
) -> VisualizationInDB:
    """Remove the public URL and take the visualization offline."""
    logger.info(f"Unpublishing visualization id={viz_id} by owner_id={owner_id}")
    doc = await db.visualizations.find_one({"_id": ObjectId(viz_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visualization not found")
    if str(doc["owner_id"]) != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can unpublish")
    if doc.get("published_slug") is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Visualization is not published")

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
        return_document=True,
    )
    logger.info(f"Visualization id={viz_id} unpublished")
    return _viz_from_doc(result)


async def get_published_by_slug(
    db: AsyncIOMotorDatabase, slug: str
) -> Optional[VisualizationInDB]:
    """Fetch a visualization by its published slug."""
    doc = await db.visualizations.find_one({"published_slug": slug})
    if doc:
        return _viz_from_doc(doc)
    return None


async def get_chat_session(
    db: AsyncIOMotorDatabase, session_id: str
) -> Optional[ChatSessionInDB]:
    doc = await db.chat_sessions.find_one({"_id": ObjectId(session_id)})
    if doc:
        return _session_from_doc(doc)
    return None


async def append_message_to_session(
    db: AsyncIOMotorDatabase, session_id: str, message: ChatMessage
) -> None:
    logger.debug(f"Appending {message.role}/{message.message_type} message to session_id={session_id} (msg_id={message.message_id})")
    now = datetime.now(timezone.utc)
    msg_doc = {
        "message_id": message.message_id,
        "role": message.role,
        "content": message.content,
        "message_type": message.message_type,
        "timestamp": message.timestamp,
        "input_tokens": message.input_tokens,
        "output_tokens": message.output_tokens,
        "cost_usd": message.cost_usd,
    }
    await db.chat_sessions.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$push": {"messages": msg_doc},
            "$set": {"updated_at": now},
        },
    )


async def update_llm_state(
    db: AsyncIOMotorDatabase, session_id: str, state: str
) -> None:
    logger.debug(f"Updating llm_state to '{state}' for session_id={session_id}")
    now = datetime.now(timezone.utc)
    await db.chat_sessions.update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"llm_state": state, "updated_at": now}},
    )


async def delete_visualization(
    db: AsyncIOMotorDatabase, viz_id: str, owner_id: str
) -> None:
    viz = await get_visualization_by_id(db, viz_id)
    if not viz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visualization not found"
        )
    if viz.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    # Delete the linked chat session first
    await db.chat_sessions.delete_one({"_id": ObjectId(viz.chat_session_id)})
    # Delete the visualization
    await db.visualizations.delete_one({"_id": ObjectId(viz_id)})
    logger.info(f"Deleted visualization id={viz_id} and its chat session id={viz.chat_session_id}")


async def add_cost_to_visualization(
    db: AsyncIOMotorDatabase, viz_id: str, cost_usd: float
) -> None:
    """Atomically increment the running total cost for a visualization."""
    await db.visualizations.update_one(
        {"_id": ObjectId(viz_id)},
        {
            "$inc": {"total_cost_usd": cost_usd},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )
    logger.debug(f"Added ${cost_usd:.6f} to viz_id={viz_id} total cost")
