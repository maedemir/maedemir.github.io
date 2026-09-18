from datetime import date, datetime

from pydantic import BaseModel, Field


class PaperOut(BaseModel):
    id: int
    uid: str
    doi: str | None
    pmid: str | None
    title: str
    abstract: str | None
    authors: list
    venue: str | None
    year: int | None
    published_date: date | None
    record_type: str
    is_preprint: bool
    is_oa: bool
    oa_status: str | None
    access_needed: bool
    pdf_url: str | None
    landing_url: str | None
    modality: str
    platforms: list
    resolution: str
    organism: str | None
    tissue: str | None
    disease_or_system: str | None
    study_type: str
    impactful_experiments: str | None
    novel_approaches: str | None
    data_availability: str | None
    code_availability: str | None
    why_it_matters: str | None
    full_text_available: bool
    sources: list

    model_config = {"from_attributes": True}


class PaperListOut(BaseModel):
    total: int
    page: int
    page_size: int
    papers: list[PaperOut]


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class AskResponse(BaseModel):
    question: str
    answer: str
    context: str | None = None
    mode: str
    degraded: bool = False
    detail: str | None = None
