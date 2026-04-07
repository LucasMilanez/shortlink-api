from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    links = relationship(
        "Link", back_populates="owner", cascade="all, delete-orphan"
    )


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    short_code = Column(String(12), unique=True, index=True, nullable=False)
    target_url = Column(String, nullable=False)
    click_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="links")
    clicks = relationship(
        "Click", back_populates="link", cascade="all, delete-orphan"
    )


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False, index=True)
    clicked_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    user_agent = Column(String, nullable=True)
    referrer = Column(String, nullable=True)

    link = relationship("Link", back_populates="clicks")
