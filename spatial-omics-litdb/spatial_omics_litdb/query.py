from __future__ import annotations

from sqlalchemy import Select, String, and_, cast, func, or_, select
from sqlalchemy.orm import Session

from spatial_omics_litdb.models import IngestRun, Paper
from spatial_omics_litdb.taxonomy import KNOWN_PLATFORMS, MODALITIES, RESOLUTIONS, STUDY_TYPES


def apply_filters(
    stmt: Select,
    q: str | None = None,
    modality: str | None = None,
    platform: str | None = None,
    resolution: str | None = None,
    study_type: str | None = None,
    organism: str | None = None,
    access: str | None = None,
    record_type: str | None = None,
) -> Select:
    conditions = []
    if q:
        like = f"%{q.strip().lower()}%"
        conditions.append(
            or_(
                Paper.search_text.ilike(like),
                Paper.title.ilike(like),
                Paper.abstract.ilike(like),
                Paper.venue.ilike(like),
            )
        )
    if modality:
        conditions.append(Paper.modality == modality)
    if resolution:
        conditions.append(Paper.resolution == resolution)
    if study_type:
        conditions.append(Paper.study_type == study_type)
    if organism:
        conditions.append(Paper.organism == organism)
    if record_type:
        conditions.append(Paper.record_type == record_type)
    if access == "oa":
        conditions.append(Paper.is_oa.is_(True))
    elif access == "needed":
        conditions.append(Paper.access_needed.is_(True))
    if platform:
        # Portable JSON membership: CAST to text and LIKE (SQLite JSON and Postgres JSON/JSONB).
        conditions.append(cast(Paper.platforms, String).ilike(f"%{platform}%"))
    if conditions:
        stmt = stmt.where(and_(*conditions))
    return stmt


def list_papers(db: Session, page: int = 1, page_size: int = 20, **filters) -> tuple[int, list[Paper]]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    base = apply_filters(select(Paper), **filters)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    stmt = (
        base.order_by(Paper.published_date.desc().nullslast(), Paper.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    papers = list(db.execute(stmt).scalars())
    return total, papers


def stats(db: Session) -> dict:
    total = db.execute(select(func.count(Paper.id))).scalar_one()
    oa = db.execute(select(func.count(Paper.id)).where(Paper.is_oa.is_(True))).scalar_one()
    preprints = db.execute(select(func.count(Paper.id)).where(Paper.is_preprint.is_(True))).scalar_one()
    by_modality = {
        row[0]: row[1]
        for row in db.execute(
            select(Paper.modality, func.count(Paper.id)).group_by(Paper.modality)
        )
    }
    last_run = db.execute(select(IngestRun).order_by(IngestRun.id.desc()).limit(1)).scalar_one_or_none()
    organisms = [
        row[0]
        for row in db.execute(
            select(Paper.organism)
            .where(Paper.organism.is_not(None))
            .group_by(Paper.organism)
            .order_by(func.count(Paper.id).desc())
        )
        if row[0]
    ]
    return {
        "total": total,
        "oa": oa,
        "preprints": preprints,
        "access_needed": db.execute(
            select(func.count(Paper.id)).where(Paper.access_needed.is_(True))
        ).scalar_one(),
        "by_modality": by_modality,
        "last_run": last_run,
        "organisms": organisms,
        "modalities": MODALITIES,
        "platforms": KNOWN_PLATFORMS,
        "resolutions": RESOLUTIONS,
        "study_types": STUDY_TYPES,
    }
