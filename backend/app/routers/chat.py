import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.mongodb import get_database
from app.models.chat import ChatMessage
from app.services.auth_service import decode_access_token
from app.services import visualization_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{viz_id}")
async def chat_websocket(websocket: WebSocket, viz_id: str, token: str = ""):
    db = get_database()
    logger.info(f"WebSocket connection attempt for viz_id={viz_id}")

    # Authenticate
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            logger.warning(f"WebSocket rejected for viz_id={viz_id}: token missing 'sub' claim")
            await websocket.close(code=4001, reason="Invalid token")
            return
    except Exception as e:
        logger.warning(f"WebSocket auth failed for viz_id={viz_id}: {e}")
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Authentication failed"})
        await websocket.close(code=4001)
        return

    logger.debug(f"WebSocket auth OK for user_id={user_id}, viz_id={viz_id}")

    # Fetch visualization
    viz = await visualization_service.get_visualization_by_id(db, viz_id)
    if not viz:
        logger.warning(f"WebSocket rejected: viz_id={viz_id} not found")
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Visualization not found"})
        await websocket.close(code=4004)
        return

    if viz.owner_id != user_id:
        logger.warning(f"WebSocket rejected: user_id={user_id} does not own viz_id={viz_id} (owner={viz.owner_id})")
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Access denied"})
        await websocket.close(code=4003)
        return

    # Get chat session
    session = await visualization_service.get_chat_session(db, viz.chat_session_id)
    if not session:
        logger.error(f"Chat session not found for viz_id={viz_id} (session_id={viz.chat_session_id})")
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Chat session not found"})
        await websocket.close(code=4004)
        return

    await websocket.accept()
    logger.info(f"WebSocket connected: user_id={user_id} viz_id={viz_id} session_id={session.id} messages={len(session.messages)}")

    # Send initial state
    await websocket.send_json({
        "type": "init",
        "session": session.model_dump(mode="json"),
    })

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            if not content:
                logger.debug(f"Empty message received on viz_id={viz_id}, ignoring")
                await websocket.send_json({
                    "type": "error",
                    "message": "Message content cannot be empty",
                })
                continue

            logger.info(f"Message received on viz_id={viz_id}: {len(content)} chars")
            logger.debug(f"Message content preview: '{content[:120]}{'...' if len(content) > 120 else ''}'")

            # Re-fetch session for latest messages
            session = await visualization_service.get_chat_session(
                db, viz.chat_session_id
            )

            # Create and store user message
            now = datetime.now(timezone.utc)
            user_msg = ChatMessage(
                message_id=str(uuid.uuid4()),
                role="user",
                content=content,
                message_type="chat",
                timestamp=now,
            )
            await visualization_service.append_message_to_session(
                db, viz.chat_session_id, user_msg
            )
            logger.debug(f"User message stored (msg_id={user_msg.message_id})")

            # Re-fetch session again (now includes the user message)
            session = await visualization_service.get_chat_session(
                db, viz.chat_session_id
            )

            # Process through LLM (Phase 1: clarification)
            logger.info(f"Sending to LLM: viz_id={viz_id}, history_len={len(session.messages)} messages")

            # Get current spec for context if editing
            current_spec = None
            current_viz = await visualization_service.get_visualization_by_id(db, viz_id)
            if current_viz and current_viz.current_draft_spec:
                current_spec = current_viz.current_draft_spec

            response_text, is_spec_ready, spec_text, phase1_usage = await llm_service.process_message(
                session, content, websocket, current_spec=current_spec
            )

            if is_spec_ready and spec_text:
                logger.info(f"Spec ready for viz_id={viz_id} ({len(spec_text)} chars), proceeding to HTML generation")

                # Store the conversational pre-text as clarification
                if response_text:
                    pre_msg = ChatMessage(
                        message_id=str(uuid.uuid4()),
                        role="assistant",
                        content=response_text,
                        message_type="clarification",
                        timestamp=datetime.now(timezone.utc),
                    )
                    await visualization_service.append_message_to_session(
                        db, viz.chat_session_id, pre_msg
                    )

                # Store spec as a message in the session (not shown in chat)
                # Attach phase 1 usage to spec_output (not the pre-text) to avoid double-counting
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
                await visualization_service.append_message_to_session(
                    db, viz.chat_session_id, spec_msg
                )

                # Accumulate phase 1 cost into the visualization total
                if phase1_usage["cost_usd"] > 0:
                    await visualization_service.add_cost_to_visualization(
                        db, viz_id, phase1_usage["cost_usd"]
                    )

                # Version the spec in the visualization document
                await visualization_service.update_draft_spec(db, viz_id, spec_text)
                logger.info(f"Spec versioned for viz_id={viz_id}")

                # Update LLM state to generating
                await visualization_service.update_llm_state(
                    db, viz.chat_session_id, "generating"
                )

                # Phase 2: Generate HTML from spec
                # Determine if this is an incremental edit (Mode B) or fresh generation (Mode A)
                current_viz = await visualization_service.get_visualization_by_id(db, viz_id)
                existing_html = None
                previous_spec = None
                if current_viz and current_viz.current_draft_html:
                    existing_html = current_viz.current_draft_html
                    previous_spec = current_spec  # current_spec holds the pre-edit spec
                    logger.info(f"Mode B (incremental edit): existing_html={len(existing_html)} chars")
                else:
                    logger.info("Mode A (fresh generation): no existing HTML")

                html_content, phase2_usage = await llm_service.generate_html_from_spec(
                    spec_text, websocket,
                    existing_html=existing_html,
                    previous_spec=previous_spec,
                )

                if html_content:
                    logger.info(f"HTML generated for viz_id={viz_id} ({len(html_content)} chars)")
                    # Store HTML output in session
                    html_msg = ChatMessage(
                        message_id=str(uuid.uuid4()),
                        role="assistant",
                        content=html_content,
                        message_type="html_output",
                        timestamp=datetime.now(timezone.utc),
                        input_tokens=phase2_usage["input_tokens"],
                        output_tokens=phase2_usage["output_tokens"],
                        cost_usd=phase2_usage["cost_usd"],
                    )
                    await visualization_service.append_message_to_session(
                        db, viz.chat_session_id, html_msg
                    )

                    # Accumulate phase 2 cost
                    if phase2_usage["cost_usd"] > 0:
                        await visualization_service.add_cost_to_visualization(
                            db, viz_id, phase2_usage["cost_usd"]
                        )

                    # Update visualization draft HTML
                    await visualization_service.update_draft_html(db, viz_id, html_content)
                    logger.info(f"Draft HTML updated for viz_id={viz_id}")

                    # Update LLM state to complete
                    await visualization_service.update_llm_state(
                        db, viz.chat_session_id, "complete"
                    )
                    logger.debug(f"LLM state set to 'complete' for session_id={viz.chat_session_id}")
                else:
                    logger.warning(f"HTML generation failed for viz_id={viz_id}, reverting to clarifying")
                    await visualization_service.update_llm_state(
                        db, viz.chat_session_id, "clarifying"
                    )
            else:
                logger.info(f"LLM clarification response for viz_id={viz_id}: {len(response_text)} chars")
                # Store assistant clarification message
                assistant_msg = ChatMessage(
                    message_id=str(uuid.uuid4()),
                    role="assistant",
                    content=response_text,
                    message_type="clarification",
                    timestamp=datetime.now(timezone.utc),
                    input_tokens=phase1_usage["input_tokens"],
                    output_tokens=phase1_usage["output_tokens"],
                    cost_usd=phase1_usage["cost_usd"],
                )
                await visualization_service.append_message_to_session(
                    db, viz.chat_session_id, assistant_msg
                )

                # Accumulate phase 1 cost into the visualization total
                if phase1_usage["cost_usd"] > 0:
                    await visualization_service.add_cost_to_visualization(
                        db, viz_id, phase1_usage["cost_usd"]
                    )

                # Update LLM state
                await visualization_service.update_llm_state(
                    db, viz.chat_session_id, "clarifying"
                )
                logger.debug(f"LLM state set to 'clarifying' for session_id={viz.chat_session_id}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for viz_id={viz_id}, user_id={user_id}")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error for viz_id={viz_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
