from fastapi import APIRouter, Depends, HTTPException, status
from database import supabase
from deps.auth import get_current_user
from schemas import FolderCreate, FolderUpdate, FolderOut
from typing import List
from datetime import datetime

router = APIRouter(
    prefix="/folders",
    tags=["folders"]
)

@router.get("/", response_model=List[FolderOut])
def list_folders(user=Depends(get_current_user)):
    """Get all folders for the current user"""
    user_id = user["id"]
    res = supabase.table("folders").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
    return res.data if res.data else []

@router.get("/{folder_id}", response_model=FolderOut)
def get_folder(folder_id: str, user=Depends(get_current_user)):
    """Get a specific folder by ID"""
    user_id = user["id"]
    res = supabase.table("folders").select("*").eq("id", folder_id).eq("user_id", user_id).single().execute()
    if res.data is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    return res.data

@router.post("/", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(payload: FolderCreate, user=Depends(get_current_user)):
    """Create a new folder"""
    user_id = user["id"]
    now = datetime.utcnow().isoformat()
    
    # Check if folder with same name already exists for this user
    existing = supabase.table("folders").select("*").eq("user_id", user_id).eq("name", payload.name).execute()
    if existing.data and len(existing.data) > 0:
        raise HTTPException(status_code=400, detail="Folder with this name already exists")
    
    data = {
        "name": payload.name.strip(),
        "user_id": user_id,
        "created_at": now,
    }
    res = supabase.table("folders").insert(data, count="exact").execute()
    if res.data:
        return res.data[0]
    raise HTTPException(status_code=500, detail="Failed to create folder")

@router.patch("/{folder_id}", response_model=FolderOut)
def update_folder(folder_id: str, payload: FolderUpdate, user=Depends(get_current_user)):
    """Update a folder (currently only name can be updated)"""
    user_id = user["id"]
    
    # Check if folder exists and belongs to user
    existing = supabase.table("folders").select("*").eq("id", folder_id).eq("user_id", user_id).single().execute()
    if existing.data is None:
        raise HTTPException(status_code=404, detail="Folder not found or not owned by user")
    
    # If updating name, check for duplicates
    if payload.name:
        name_check = supabase.table("folders").select("*").eq("user_id", user_id).eq("name", payload.name.strip()).neq("id", folder_id).execute()
        if name_check.data and len(name_check.data) > 0:
            raise HTTPException(status_code=400, detail="Folder with this name already exists")
    
    update_data = payload.dict(exclude_unset=True, exclude_none=True)
    if "name" in update_data:
        update_data["name"] = update_data["name"].strip()
    
    res = supabase.table("folders").update(update_data).eq("id", folder_id).eq("user_id", user_id).execute()
    if res.data is None or len(res.data) == 0:
        raise HTTPException(status_code=404, detail="Folder not found or not owned by user")
    return res.data[0]

@router.delete("/{folder_id}")
def delete_folder(folder_id: str, user=Depends(get_current_user)):
    """Delete a folder and optionally handle associated notes"""
    user_id = user["id"]
    
    # Check if folder exists and belongs to user
    existing = supabase.table("folders").select("*").eq("id", folder_id).eq("user_id", user_id).single().execute()
    if existing.data is None:
        raise HTTPException(status_code=404, detail="Folder not found or not owned by user")
    
    # Optional: Update notes in this folder to have no folder (set folder_id to None)
    # This prevents orphaned notes when folder is deleted
    supabase.table("notes").update({"folder_id": None}).eq("folder_id", folder_id).eq("user_id", user_id).execute()
    
    # Delete the folder
    res = supabase.table("folders").delete().eq("id", folder_id).eq("user_id", user_id).execute()
    return {"message": "Folder deleted successfully"}
