import logging
from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for declarative models."""


links_tags = Table(
    "links_tags",
    Base.metadata,
    Column("link_id", ForeignKey("tracked_links.link_id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.tag_id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("link_id", "tag_id", name="unique_link_tag"),
)


class UserORM(Base):
    """ORM model for users."""

    __tablename__ = "users"

    chat_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    links: Mapped[List["LinkORM"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("idx_users_chat_id", "chat_id"),)


class TagORM(Base):
    """ORM model for tags."""

    __tablename__ = "tags"

    tag_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tag_name: Mapped[str] = mapped_column("tag_name", String(100), unique=True)
    links: Mapped[List["LinkORM"]] = relationship(secondary=links_tags, back_populates="tags")


class LinkMuteStatusORM(Base):
    """ORM model for link mute statuses."""

    __tablename__ = "link_mute_statuses"

    mute_status_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    link_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tracked_links.link_id", ondelete="CASCADE"),
        nullable=False,
    )
    chat_id: Mapped[int] = mapped_column(Integer, nullable=False)
    muted: Mapped[bool] = mapped_column(Boolean, default=False)

    link: Mapped["LinkORM"] = relationship("LinkORM", back_populates="mute_status")

    __table_args__ = (Index("idx_link_mute_statuses_link_id", "link_id"),)


class LinkORM(Base):
    """ORM model for tracked links."""

    __tablename__ = "tracked_links"

    link_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("users.chat_id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(255))
    last_updated: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    filters: Mapped[str | None] = mapped_column(String(255))

    user: Mapped["UserORM"] = relationship(back_populates="links")
    tags: Mapped[List[TagORM]] = relationship(
        secondary="links_tags",
        back_populates="links",
        lazy="selectin",
    )
    mute_status: Mapped["LinkMuteStatusORM"] = relationship(
        "LinkMuteStatusORM",
        back_populates="link",
        uselist=False,
        lazy="joined",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("chat_id", "url", name="unique_chat_url"),
        Index("idx_tracked_links_last_updated", "last_updated"),
        Index("idx_tracked_links_chat_id", "chat_id"),
    )
