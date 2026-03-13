from datetime import datetime
from typing import Literal, List, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    message_id: str
    role: Literal["user", "assistant"]
    content: str
    message_type: Literal["chat", "clarification", "html_output", "spec_output"]
    timestamp: datetime
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost_usd: Optional[float] = None


class ChatSessionInDB(BaseModel):
    id: str
    visualization_id: str
    owner_id: str
    messages: List[ChatMessage] = []
    llm_state: Literal["clarifying", "generating", "complete"]
    created_at: datetime
    updated_at: datetime


class UserChatInput(BaseModel):
    content: str
