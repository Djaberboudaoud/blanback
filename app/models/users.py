from sqlalchemy import Column, Integer, String
from app.core.database import Base


class User(Base):
    """Renamed from Admins → Users, with a role column added."""
    __tablename__ = "users"

    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    phone    = Column(String(20), nullable=False)
    email    = Column(String(100), unique=True, index=True, nullable=False)
    # role: admin | seller | buyer
    role     = Column(String(20), nullable=False, default="buyer")
