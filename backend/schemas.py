# backend/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class NoteBase(BaseModel):
    title: Optional[str] = ""
    content: Optional[str] = ""
    is_starred: bool = False
    is_pinned: bool = False
    is_trashed: bool = False

class NoteCreate(NoteBase):
    # user_id is validated server-side via JWT — not strictly necessary to pass, but frontend may include
    user_id: Optional[str] = None

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_starred: Optional[bool] = None
    is_pinned: Optional[bool] = None
    is_trashed: Optional[bool] = None
    folder_id: Optional[str] = None

    class Config:
        extra = "ignore"  # Ignore any extra fields sent by frontend

class NoteOut(NoteBase):
    id: str
    user_id: str
    folder_id: Optional[str]
    is_starred: bool
    is_pinned: bool
    is_trashed: bool
    created_at: datetime
    updated_at: datetime

# Folder schemas
class FolderBase(BaseModel):
    name: str

class FolderCreate(FolderBase):
    pass

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    
    class Config:
        extra = "ignore"

class FolderOut(FolderBase):
    id: str
    name: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── Chat schemas ─────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str          # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    query: str
    folder_id: Optional[str] = None
    search_mode: str = "hybrid"           # "semantic" | "keyword" | "hybrid"
    top_k: int = 5
    conversation_history: Optional[List[ChatMessage]] = None

class SourceCitationOut(BaseModel):
    note_id: str
    title: str
    snippet: str
    score: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitationOut]
    search_mode: str
    chunks_retrieved: int
    cache_hit: bool = False
