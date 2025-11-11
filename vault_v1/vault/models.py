from __future__ import annotations

from datetime import datetime
from typing import Generator

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    files: Mapped[list["File"]] = relationship(secondary="file_chunks", back_populates="chunks")


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    uploader: Mapped[str | None] = mapped_column(String(128), nullable=True)
    total_size: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    merkle_root: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    chunks: Mapped[list[Chunk]] = relationship(
        secondary="file_chunks",
        back_populates="files",
        viewonly=True,
    )
    file_chunks: Mapped[list["FileChunk"]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
        overlaps="files",
    )
    receipts: Mapped[list["Receipt"]] = relationship(back_populates="file", cascade="all, delete-orphan")


class FileChunk(Base):
    __tablename__ = "file_chunks"
    __table_args__ = (UniqueConstraint("file_id", "position", name="uq_file_chunk_position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    file: Mapped[File] = relationship(back_populates="file_chunks", overlaps="files")
    chunk: Mapped[Chunk] = relationship(overlaps="files")


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    receipt_type: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    signature: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    file: Mapped[File] = relationship(back_populates="receipts")


_engine = None
SessionLocal = sessionmaker(expire_on_commit=False, class_=Session)


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url)
        SessionLocal.configure(bind=_engine)
        Base.metadata.create_all(bind=_engine)
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None
    SessionLocal.configure(bind=None)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal(bind=get_engine())
    try:
        yield session
    finally:
        session.close()


__all__ = [
    "Base",
    "Chunk",
    "File",
    "FileChunk",
    "Receipt",
    "SessionLocal",
    "get_engine",
    "reset_engine",
    "get_session",
]
