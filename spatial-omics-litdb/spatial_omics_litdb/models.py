from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


# JSON works on SQLite; JSONB is used automatically on Postgres.
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Paper(Base):
    __tablename__ = "papers"
    __table_args__ = (
        UniqueConstraint("uid", name="uq_papers_uid"),
        Index("ix_papers_doi", "doi"),
        Index("ix_papers_published_date", "published_date"),
        Index("ix_papers_modality", "modality"),
        Index("ix_papers_study_type", "study_type"),
        Index("ix_papers_is_oa", "is_oa"),
        Index("ix_papers_is_preprint", "is_preprint"),
        Index("ix_papers_year", "year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(512), nullable=False)

    doi: Mapped[str | None] = mapped_column(String(256))
    pmid: Mapped[str | None] = mapped_column(String(32))
    pmcid: Mapped[str | None] = mapped_column(String(32))
    openalex_id: Mapped[str | None] = mapped_column(String(256))
    preprint_id: Mapped[str | None] = mapped_column(String(256))

    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text)
    authors: Mapped[list] = mapped_column(JSONType, default=list)
    venue: Mapped[str | None] = mapped_column(String(512))
    year: Mapped[int | None] = mapped_column(Integer)
    published_date: Mapped[date | None] = mapped_column(Date)

    record_type: Mapped[str] = mapped_column(String(32), default="other")
    is_preprint: Mapped[bool] = mapped_column(Boolean, default=False)
    is_oa: Mapped[bool] = mapped_column(Boolean, default=False)
    oa_status: Mapped[str | None] = mapped_column(String(32))
    access_needed: Mapped[bool] = mapped_column(Boolean, default=True)
    pdf_url: Mapped[str | None] = mapped_column(Text)
    landing_url: Mapped[str | None] = mapped_column(Text)
    license: Mapped[str | None] = mapped_column(String(256))

    modality: Mapped[str] = mapped_column(String(32), default="unknown")
    platforms: Mapped[list] = mapped_column(JSONType, default=list)
    resolution: Mapped[str] = mapped_column(String(32), default="unknown")
    organism: Mapped[str | None] = mapped_column(String(128))
    tissue: Mapped[str | None] = mapped_column(String(256))
    disease_or_system: Mapped[str | None] = mapped_column(String(256))
    study_type: Mapped[str] = mapped_column(String(32), default="unknown")

    impactful_experiments: Mapped[str | None] = mapped_column(Text)
    novel_approaches: Mapped[str | None] = mapped_column(Text)
    data_availability: Mapped[str | None] = mapped_column(Text)
    code_availability: Mapped[str | None] = mapped_column(Text)
    why_it_matters: Mapped[str | None] = mapped_column(Text)

    pdf_path: Mapped[str | None] = mapped_column(Text)
    full_text_available: Mapped[bool] = mapped_column(Boolean, default=False)
    sources: Mapped[list] = mapped_column(JSONType, default=list)
    search_text: Mapped[str | None] = mapped_column(Text)

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IngestRun(Base):
    __tablename__ = "ingest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="running")
    source_filter: Mapped[str | None] = mapped_column(String(64))
    records_seen: Mapped[int] = mapped_column(Integer, default=0)
    records_upserted: Mapped[int] = mapped_column(Integer, default=0)
    pdfs_downloaded: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
