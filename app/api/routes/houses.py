import os
import uuid
import requests

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.config import settings
from app.core.database import get_db
from app.schema.houses import HouseCreate, HouseUpdate, HouseResponse, HouseImageResponse
from app.crud import houses as houses_crud
from app.api.depandance import get_current_user

router = APIRouter()

# Supabase Storage Bucket name
SUPABASE_BUCKET = "photos"

def delete_supabase_file(image_path: str):
    """Helper to delete a file from Supabase Storage"""
    if not image_path.startswith("http"):
        return
    
    # Extract filename from URL (e.g. https://.../storage/v1/object/public/photos/abc.jpg)
    filename = image_path.split("/")[-1]
    
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "apikey": settings.SUPABASE_KEY,
    }
    try:
        requests.delete(url, headers=headers)
    except Exception as e:
        print("Failed to delete from Supabase:", e)


# ─────────────────────────────────────────────────────────────────────────────
# HOUSE CRUD
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[HouseResponse])
def list_houses(
    skip:  int = Query(0,   ge=0),
    limit: int = Query(20,  ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Return all houses (public — no login needed)."""
    return houses_crud.get_all_houses(db, skip=skip, limit=limit)


@router.get("/my", response_model=List[HouseResponse])
def get_my_houses(
    skip:  int = Query(0,   ge=0),
    limit: int = Query(20,  ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return all houses for the logged in seller."""
    return houses_crud.get_houses_by_seller(db, seller_id=current_user.id, skip=skip, limit=limit)


@router.get("/pending", response_model=List[HouseResponse])
def get_pending_houses(
    skip:  int = Query(0,   ge=0),
    limit: int = Query(20,  ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Admin only: return all houses under review."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return houses_crud.get_pending_houses(db, skip=skip, limit=limit)


@router.get("/{house_id}", response_model=HouseResponse)
def get_house(
    house_id: int,
    db: Session = Depends(get_db),
):
    """Return one house by ID."""
    house = houses_crud.get_house_by_id(db, house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return house


@router.post("/", response_model=HouseResponse, status_code=status.HTTP_201_CREATED)
def create_house(
    house: HouseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),       # 🔒 must be logged in
):
    """Create a new house listing. Starts as Under_review."""
    return houses_crud.create_house(db, house, seller_id=current_user.id)


@router.put("/{house_id}", response_model=HouseResponse)
def update_house(
    house_id: int,
    house: HouseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),       # 🔒 must be logged in
):
    """Update any fields of a house. When status → Sold, image files are deleted from disk."""
    existing = houses_crud.get_house_by_id(db, house_id)
    if not existing:
        raise HTTPException(status_code=404, detail="House not found")
    if existing.seller_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to edit this house")

    # Collect image paths if transitioning to Sold
    is_selling = house.status is not None and house.status.value == "Sold"
    image_paths = [img.image_path for img in existing.images] if is_selling else []

    updated = houses_crud.update_house(db, house_id, house)
    if not updated:
        raise HTTPException(status_code=404, detail="House not found")

    # After marking as Sold, delete image files from Supabase and their DB records
    if is_selling:
        for path in image_paths:
            delete_supabase_file(path)
        # Remove from DB
        from app.models.houses import HouseImage
        db.query(HouseImage).filter(HouseImage.house_id == house_id).delete(synchronize_session=False)
        db.commit()

    return updated


@router.delete("/{house_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_house(
    house_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),       # 🔒 must be logged in
):
    """Delete a house, all its DB images, AND the physical files on disk."""
    existing = houses_crud.get_house_by_id(db, house_id)
    if not existing:
        raise HTTPException(status_code=404, detail="House not found")
    if existing.seller_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this house")

    # Collect image paths BEFORE deleting DB rows
    image_paths = [img.image_path for img in existing.images]

    deleted = houses_crud.delete_house(db, house_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="House not found")

    # Remove physical files from Supabase
    for path in image_paths:
        delete_supabase_file(path)



@router.put("/{house_id}/approve", response_model=HouseResponse)
def approve_house(
    house_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    from app.schema.houses import HouseStatus as HS
    update_data = HouseUpdate(status=HS.available)
    updated = houses_crud.update_house(db, house_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="House not found")
    return updated

@router.put("/{house_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
def reject_house(
    house_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    # Collect image paths before deletion
    existing = houses_crud.get_house_by_id(db, house_id)
    if not existing:
        raise HTTPException(status_code=404, detail="House not found")
    image_paths = [img.image_path for img in existing.images]
    deleted = houses_crud.delete_house(db, house_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="House not found")
    # Remove physical files
    for path in image_paths:
        delete_supabase_file(path)

# ─────────────────────────────────────────────────────────────────────────────
# IMAGE UPLOAD / DELETE
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/{house_id}/images",
    response_model=HouseImageResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_image(
    house_id: int,
    file:     UploadFile = File(...),
    is_cover: bool       = Form(False),
    db:       Session    = Depends(get_db),
    current_user=Depends(get_current_user),           # 🔒 must be logged in
):
    """
    Upload one image for a house.
    - `file`     : the image file (jpg, png, webp …)
    - `is_cover` : set True to make this the cover photo
    """
    # Make sure the house exists
    house = houses_crud.get_house_by_id(db, house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    if house.seller_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to edit this house")

    # Validate file type
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file.content_type}' not allowed. Use jpeg, png, webp or gif.",
        )

    # Upload to Supabase Storage
    ext       = os.path.splitext(file.filename or "image.jpg")[1]
    filename  = f"{uuid.uuid4().hex}{ext}"
    
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "apikey": settings.SUPABASE_KEY,
        "Content-Type": file.content_type,
    }
    
    # Read file content
    file_bytes = file.file.read()
    
    response = requests.post(url, headers=headers, data=file_bytes)
    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=500,
            detail=f"Supabase upload failed [{response.status_code}]: {response.text}"
        )
        
    # The public URL for the uploaded image
    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"

    # Store the relative path in the database
    db_image = houses_crud.add_image(
        db,
        house_id=house_id,
        image_path=public_url,
        is_cover=is_cover,
    )
    return db_image


@router.get("/{house_id}/images", response_model=List[HouseImageResponse])
def list_images(
    house_id: int,
    db: Session = Depends(get_db),
):
    """Return all images for a house."""
    house = houses_crud.get_house_by_id(db, house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return houses_crud.get_images_by_house(db, house_id)


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),       # 🔒 must be logged in
):
    """Delete a single image by its ID."""
    # Fetch image first directly with db.query
    from app.models.houses import HouseImage, House
    img = db.query(HouseImage).filter(HouseImage.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    house = db.query(House).filter(House.id == img.house_id).first()
    if house.seller_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    deleted = houses_crud.delete_image(db, image_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found")
    # Also remove the file from Supabase
    delete_supabase_file(deleted.image_path)
