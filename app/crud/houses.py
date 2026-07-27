from sqlalchemy.orm import Session
from app.models.houses import House, HouseImage
from app.schema.houses import HouseCreate, HouseUpdate


# ── House CRUD ─────────────────────────────────────────────────────────────────

def get_all_houses(db: Session, skip: int = 0, limit: int = 100):
    """Return a paginated list of all Available houses."""
    from app.schema.houses import HouseStatus
    return db.query(House).filter(House.status == HouseStatus.available.value).offset(skip).limit(limit).all()

def get_houses_by_seller(db: Session, seller_id: int, skip: int = 0, limit: int = 100):
    """Return all houses for a specific seller (any status)."""
    return db.query(House).filter(House.seller_id == seller_id).offset(skip).limit(limit).all()

def get_pending_houses(db: Session, skip: int = 0, limit: int = 100):
    """Return all houses that are Under_review."""
    from app.schema.houses import HouseStatus
    return db.query(House).filter(House.status == HouseStatus.under_review.value).offset(skip).limit(limit).all()


def get_house_by_id(db: Session, house_id: int):
    """Return a single house by ID (or None if not found)."""
    return db.query(House).filter(House.id == house_id).first()


def create_house(db: Session, house: HouseCreate, seller_id: int):
    db_house = House(
        address=house.address,
        description=house.description,
        price=house.price,
        status="Under_review", # Always start as under_review
        type=house.type,
        offer=house.offer,
        seller_id=seller_id,
    )
    db.add(db_house)
    db.commit()
    db.refresh(db_house)
    return db_house


def update_house(db: Session, house_id: int, house: HouseUpdate):
    """Partially update a house. Only fields that are sent get changed."""
    db_house = get_house_by_id(db, house_id)
    if not db_house:
        return None
    update_data = house.model_dump(exclude_unset=True)
    # Convert enum → string value before saving
    if "status" in update_data and update_data["status"] is not None:
        update_data["status"] = update_data["status"].value
    for key, value in update_data.items():
        setattr(db_house, key, value)
    db.commit()
    db.refresh(db_house)
    return db_house


def delete_house(db: Session, house_id: int):
    """Delete a house (images deleted automatically via CASCADE)."""
    db_house = get_house_by_id(db, house_id)
    if not db_house:
        return None
    db.delete(db_house)
    db.commit()
    return db_house


# ── HouseImage CRUD ────────────────────────────────────────────────────────────

def add_image(db: Session, house_id: int, image_path: str, is_cover: bool = False):
    """Save one uploaded image record for a house."""
    # If this image is the cover, clear any existing cover first
    if is_cover:
        db.query(HouseImage).filter(
            HouseImage.house_id == house_id,
            HouseImage.is_cover == True,
        ).update({"is_cover": False})

    db_image = HouseImage(
        house_id=house_id,
        image_path=image_path,
        is_cover=is_cover,
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


def get_images_by_house(db: Session, house_id: int):
    """Return all images belonging to a house."""
    return db.query(HouseImage).filter(HouseImage.house_id == house_id).all()


def delete_image(db: Session, image_id: int):
    """Delete a single image record."""
    db_image = db.query(HouseImage).filter(HouseImage.id == image_id).first()
    if not db_image:
        return None
    db.delete(db_image)
    db.commit()
    return db_image
