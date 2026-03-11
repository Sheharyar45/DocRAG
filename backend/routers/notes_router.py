from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from database import supabase
from deps.auth import get_current_user
from schemas import NoteCreate, NoteUpdate, NoteOut
from services.ingestion_service import get_ingestion_service
from typing import List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/notes",
    tags=["notes"]
)

async def index_note_background(note_id: str, title: str, content: str, user_id: str, folder_id: Optional[str] = None, tags: Optional[List[str]] = None):
    """Background task to index a note."""
    logger.info(f"Starting indexing for note {note_id}")
    try:
        ingestion = get_ingestion_service()
        result = await ingestion.ingest_note(note_id, title, content, user_id, folder_id, tags or [])
        logger.info(f"Indexing result for note {note_id}: success={result.success}, chunks={result.chunks_created}, error={result.error}")
    except Exception as e:
        logger.error(f"Indexing failed for note {note_id}: {e}")


async def delete_note_index_background(note_id: str, user_id: str):
    """Background task to delete note from index."""
    ingestion = get_ingestion_service()
    await ingestion.delete_note(note_id, user_id)


@router.get("/", response_model=List[NoteOut])
def list_notes(user=Depends(get_current_user), folder_id: Optional[str] = None):
    user_id = user["id"]
    query = supabase.table("notes").select("*").eq("user_id", user_id)
    if folder_id:
        query = query.eq("folder_id", folder_id)
    res = query.order("updated_at", desc=True).execute()
    return res.data if res.data else []

@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: str, user=Depends(get_current_user)):
    user_id = user["id"]
    res = supabase.table("notes").select("*").eq("id", note_id).eq("user_id", user_id).single().execute()
    if res.data is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return res.data


@router.post("/", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    user_id = user["id"]
    now = datetime.utcnow().isoformat()
    data = {
        "title": payload.title or "",
        "content": payload.content or "",
        "user_id": user_id,
        "folder_id": None,
        "created_at": now,
        "updated_at": now,
        "is_starred": payload.is_starred if payload.is_starred is not None else False,
        "is_pinned": payload.is_pinned if payload.is_pinned is not None else False,
        "is_trashed": payload.is_trashed if payload.is_trashed is not None else False,
    }
    res = supabase.table("notes").insert(data, count="exact").execute()
    if res.data:
        note = res.data[0]
        logger.info(f"Created note {note['id']} with content length: {len(note.get('content', ''))}")
        # Index in background
        if note.get("content"):
            logger.info(f"Adding indexing task for note {note['id']}")
            background_tasks.add_task(
                index_note_background,
                note["id"],
                note.get("title", ""),
                note.get("content", ""),
                user_id,
                note.get("folder_id")
            )
        return note
    raise HTTPException(status_code=500, detail="Failed to create note")

@router.patch("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: str,
    payload: NoteUpdate,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    skip_indexing: bool = Query(False, description="Skip re-indexing (for auto-save)")
):
    user_id = user["id"]
    update_data = payload.dict(exclude_unset=True, exclude_none=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()
    res = supabase.table("notes").update(update_data).eq("id", note_id).eq("user_id", user_id).execute()
    if res.data is None or len(res.data) == 0:
        raise HTTPException(status_code=404, detail="Note not found or not owned by user")
    
    note = res.data[0]
    logger.info(f"Updated note {note['id']} (skip_indexing={skip_indexing})")
    
    # Only re-index if explicitly requested (manual save, not auto-save)
    if not skip_indexing and ("content" in update_data or "title" in update_data):
        content = note.get("content", "")
        if content and len(content.strip()) >= 10:
            logger.info(f"Adding re-indexing task for note {note['id']}")
            background_tasks.add_task(
                index_note_background,
                note["id"],
                note.get("title", ""),
                content,
                user_id,
                note.get("folder_id")
            )
    else:
        logger.info(f"Skipping re-index for note {note['id']}")
    
    return note


@router.delete("/{note_id}")
async def delete_note(
    note_id: str,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    user_id = user["id"]
    res = supabase.table("notes").delete().eq("id", note_id).eq("user_id", user_id).execute()
    
    # Delete from index in background
    background_tasks.add_task(delete_note_index_background, note_id, user_id)
    
    return {"message": "Note deleted successfully"}


@router.post("/{note_id}/reindex")
async def reindex_note(
    note_id: str,
    user=Depends(get_current_user)
):
    """Manually trigger re-indexing of a note."""
    user_id = user["id"]
    
    # Get the note
    res = supabase.table("notes").select("*").eq("id", note_id).eq("user_id", user_id).single().execute()
    if res.data is None:
        raise HTTPException(status_code=404, detail="Note not found")
    
    note = res.data
    ingestion = get_ingestion_service()
    result = await ingestion.ingest_note(
        note_id=note["id"],
        title=note.get("title", ""),
        content=note.get("content", ""),
        user_id=user_id,
        folder_id=note.get("folder_id")
    )
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    
    return {"message": f"Indexed {result.chunks_created} chunks", "chunks": result.chunks_created}