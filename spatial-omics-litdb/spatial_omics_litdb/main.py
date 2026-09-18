from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from spatial_omics_litdb.config import Settings, get_settings
from spatial_omics_litdb.db import get_db_dep, init_db, make_engine, session_factory
from spatial_omics_litdb.models import Paper
from spatial_omics_litdb.qa import ask_corpus
from spatial_omics_litdb.query import list_papers, stats as corpus_stats
from spatial_omics_litdb.schemas import AskResponse, PaperListOut, PaperOut

PACKAGE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = make_engine(settings)
    init_db(engine)
    factory = session_factory(engine)
    app = FastAPI(
        title="Spatial Omics Literature Database",
        description="Living dashboard of spatial transcriptomics and spatial proteomics papers (2025–).",
        version="0.1.0",
    )
    app.state.settings = settings
    app.mount("/static", StaticFiles(directory=str(PACKAGE_DIR / "static")), name="static")
    db_dep = get_db_dep(factory)

    def _filter_kwargs(
        q: str | None,
        modality: str | None,
        platform: str | None,
        resolution: str | None,
        study_type: str | None,
        organism: str | None,
        access: str | None,
        record_type: str | None,
    ) -> dict:
        return {
            "q": q or None,
            "modality": modality or None,
            "platform": platform or None,
            "resolution": resolution or None,
            "study_type": study_type or None,
            "organism": organism or None,
            "access": access or None,
            "record_type": record_type or None,
        }

    @app.get("/health")
    def health():
        return {"ok": True, "openai": settings.has_openai}

    @app.get("/", response_class=HTMLResponse)
    def dashboard(
        request: Request,
        q: str | None = None,
        modality: str | None = None,
        platform: str | None = None,
        resolution: str | None = None,
        study_type: str | None = None,
        organism: str | None = None,
        access: str | None = None,
        record_type: str | None = None,
        page: int = 1,
        db: Session = Depends(db_dep),
    ):
        filters = _filter_kwargs(
            q, modality, platform, resolution, study_type, organism, access, record_type
        )
        total, papers = list_papers(db, page=page, page_size=20, **filters)
        summary = corpus_stats(db)
        pages = max((total + 19) // 20, 1)
        query = {k: v for k, v in filters.items() if v}

        def page_url(p: int) -> str:
            params = dict(query)
            if p > 1:
                params["page"] = p
            return "/?" + urlencode(params) if params else "/"

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "papers": papers,
                "total": total,
                "page": page,
                "pages": pages,
                "filters": filters,
                "stats": summary,
                "has_openai": settings.has_openai,
                "page_url": page_url,
            },
        )

    @app.get("/papers/{paper_id}", response_class=HTMLResponse)
    def paper_page(request: Request, paper_id: int, db: Session = Depends(db_dep)):
        paper = db.get(Paper, paper_id)
        if paper is None:
            raise HTTPException(status_code=404, detail="Paper not found")
        return templates.TemplateResponse(
            request=request,
            name="paper.html",
            context={"paper": paper, "has_openai": settings.has_openai, "stats": corpus_stats(db)},
        )

    @app.get("/ask", response_class=HTMLResponse)
    def ask_get(request: Request, db: Session = Depends(db_dep)):
        return templates.TemplateResponse(
            request=request,
            name="ask.html",
            context={
                "has_openai": settings.has_openai,
                "result": None,
                "question": "",
                "stats": corpus_stats(db),
            },
        )

    @app.post("/ask", response_class=HTMLResponse)
    def ask_post(
        request: Request,
        question: str = Form(...),
        db: Session = Depends(db_dep),
    ):
        result = ask_corpus(db, settings, question)
        return templates.TemplateResponse(
            request=request,
            name="ask.html",
            context={
                "has_openai": settings.has_openai,
                "result": result,
                "question": question,
                "stats": corpus_stats(db),
            },
        )

    @app.get("/api/papers", response_model=PaperListOut)
    def api_papers(
        q: str | None = None,
        modality: str | None = None,
        platform: str | None = None,
        resolution: str | None = None,
        study_type: str | None = None,
        organism: str | None = None,
        access: str | None = None,
        record_type: str | None = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        db: Session = Depends(db_dep),
    ):
        filters = _filter_kwargs(
            q, modality, platform, resolution, study_type, organism, access, record_type
        )
        total, papers = list_papers(db, page=page, page_size=page_size, **filters)
        return PaperListOut(
            total=total,
            page=page,
            page_size=page_size,
            papers=[PaperOut.model_validate(p) for p in papers],
        )

    @app.get("/api/papers/{paper_id}", response_model=PaperOut)
    def api_paper(paper_id: int, db: Session = Depends(db_dep)):
        paper = db.get(Paper, paper_id)
        if paper is None:
            raise HTTPException(status_code=404, detail="Paper not found")
        return PaperOut.model_validate(paper)

    @app.get("/api/stats")
    def api_stats(db: Session = Depends(db_dep)):
        summary = corpus_stats(db)
        last = summary["last_run"]
        return {
            "total": summary["total"],
            "oa": summary["oa"],
            "preprints": summary["preprints"],
            "access_needed": summary["access_needed"],
            "by_modality": summary["by_modality"],
            "openai_configured": settings.has_openai,
            "last_ingest": None
            if last is None
            else {
                "status": last.status,
                "finished_at": last.finished_at,
                "records_upserted": last.records_upserted,
            },
        }

    @app.post("/api/ask", response_model=AskResponse)
    def api_ask(payload: dict, db: Session = Depends(db_dep)):
        question = (payload or {}).get("question") or ""
        if len(question.strip()) < 3:
            raise HTTPException(status_code=400, detail="Question is too short")
        return AskResponse(**ask_corpus(db, settings, question.strip()))

    @app.post("/api/ingest")
    def api_ingest(request: Request, db: Session = Depends(db_dep)):
        token = settings.ingest_token
        if not token:
            raise HTTPException(
                status_code=503,
                detail="Set INGEST_TOKEN to enable the HTTP ingest trigger.",
            )
        auth = request.headers.get("authorization") or ""
        if auth != f"Bearer {token}":
            raise HTTPException(status_code=401, detail="Invalid ingest token")
        from spatial_omics_litdb.ingest.pipeline import run_ingest

        run = run_ingest(db, settings, download_pdfs=True)
        return {
            "status": run.status,
            "records_seen": run.records_seen,
            "records_upserted": run.records_upserted,
            "pdfs_downloaded": run.pdfs_downloaded,
        }

    @app.get("/favicon.ico")
    def favicon():
        return RedirectResponse("/static/css/app.css", status_code=302)

    return app


app = create_app()
