from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Numeric, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class House(Base):
    __tablename__ = "houses"

    id           = Column(Integer, primary_key=True, index=True)
    address      = Column(String(255), nullable=False)
    description  = Column(Text, nullable=False)
    seller_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at   = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    price        = Column(Numeric(12, 2), nullable=False)
    # ── NEW COLUMNS ───────────────────────────────────────────────────────────
    type         = Column(String(30), nullable=False, default="residential")
    # residential | commercial | agriculture | land
    offer        = Column(String(20), nullable=False, default="Rental")
    # Rental | Sale
    status       = Column(String(20), nullable=False, default="Available")
    # Available | Sold

    # one house → many images
    images = relationship("HouseImage", back_populates="house", cascade="all, delete-orphan")
    seller = relationship("User", backref="houses")

    @property
    def seller_name(self):
        return self.seller.username if self.seller else "Unknown"

    @property
    def seller_phone(self):
        return self.seller.phone if self.seller else "Unknown"


class HouseImage(Base):
    __tablename__ = "houseimages"

    id         = Column(Integer, primary_key=True, index=True)
    house_id   = Column(Integer, ForeignKey("houses.id", ondelete="CASCADE"), nullable=False)
    image_path = Column(String(255), nullable=False)
    is_cover   = Column(Boolean, default=False)

    house = relationship("House", back_populates="images")