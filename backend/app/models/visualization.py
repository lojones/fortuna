from datetime import datetime
from typing import Optional, Literal, List
from pydantic import BaseModel


class SpecVersion(BaseModel):
    version_number: int
    spec_text: str
    created_at: datetime


class PublishedVersion(BaseModel):
    version_number: int
    html_content: str
    spec_version: Optional[int] = None
    published_at: datetime
    published_by: str


class VisualizationBase(BaseModel):
    title: str
    description: Optional[str] = None


class VisualizationCreate(VisualizationBase):
    pass


class VisualizationInDB(VisualizationBase):
    id: str
    owner_id: str
    status: Literal["draft", "published"]
    current_draft_html: Optional[str] = None
    current_draft_spec: Optional[str] = None
    spec_versions: List[SpecVersion] = []
    latest_spec_version: Optional[int] = None
    published_versions: List[PublishedVersion] = []
    latest_published_version: Optional[int] = None
    published_slug: Optional[str] = None
    published_html: Optional[str] = None
    published_version_number: Optional[int] = None
    published_at: Optional[datetime] = None
    chat_session_id: str
    total_cost_usd: float = 0.0
    created_at: datetime
    updated_at: datetime


class VisualizationPublic(VisualizationInDB):
    pass
