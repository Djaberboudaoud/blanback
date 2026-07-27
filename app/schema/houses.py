from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Enums ──────────────────────────────────────────────────────────────────────

class HouseStatus(str, Enum):
    available    = "Available"
    sold         = "Sold"
    under_review = "Under_review"


# ── HouseImage Schemas ─────────────────────────────────────────────────────────

class HouseImageResponse(BaseModel):
    id:         int
    house_id:   int
    image_path: str
    is_cover:   bool

    model_config = {"from_attributes": True}


# ── House Schemas ──────────────────────────────────────────────────────────────

class HouseBase(BaseModel):
    address:      str     = Field(..., min_length=3, max_length=255)
    description:  str     = Field(..., min_length=3, max_length=1000)
    price:        Decimal = Field(..., gt=0)
    status:       HouseStatus = HouseStatus.under_review
    type:         str     = "residential"
    offer:        str     = "Rental"


class HouseCreate(HouseBase):
    """Used when creating a house. Status is forced by backend."""
    pass


class HouseUpdate(BaseModel):
    """All fields optional — send only what you want to change."""
    address:      Optional[str]         = Field(None, min_length=3, max_length=255)
    description:  Optional[str]         = Field(None, min_length=3, max_length=1000)
    price:        Optional[Decimal]     = Field(None, gt=0)
    status:       Optional[HouseStatus] = None
    type:         Optional[str]         = None
    offer:        Optional[str]         = None


class HouseResponse(HouseBase):
    """Full house response — reads seller info via SQLAlchemy relationship."""
    id:           int
    seller_id:    int
    seller_name:  str = ""
    seller_phone: str = ""
    created_at:   datetime
    images:       List[HouseImageResponse] = []

    model_config = {"from_attributes": True}
