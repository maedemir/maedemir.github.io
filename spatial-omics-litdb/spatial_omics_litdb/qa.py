from __future__ import annotations

import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from spatial_omics_litdb.config import Settings
from spatial_omics_litdb.models import Paper


def _degraded(question: str, detail: str, extra: str = "") -> dict:
    answer = (
        "PaperQA2 is not running yet. "
        + detail
        + " Discovery and the searchable dashboard still work without this key."
    )
    if extra:
        answer += "\n\n" + extra
    return {
        "question": question,
        "answer": answer,
        "context": extra or None,
        "mode": "degraded",
        "degraded": True,
        "detail": detail,
    }


def _lexical_hits(db: Session, question: str, limit: int = 6) -> list[Paper]:
    tokens = [t for t in re.findall(r"[a-zA-Z0-9]{3,}", question.lower()) if t not in {
        "the", "and", "for", "with", "what", "which", "that", "this", "from", "are"
    }]
    if not tokens:
        return []
    clauses = [Paper.search_text.ilike(f"%{token}%") for token in tokens[:8]]
    stmt = select(Paper).where(or_(*clauses)).order_by(Paper.published_date.desc()).limit(limit)
    return list(db.execute(stmt).scalars())


def ask_corpus(db: Session, settings: Settings, question: str) -> dict:
    pdfs = list(settings.pdf_dir.glob("*.pdf")) if settings.pdf_dir.exists() else []
    hits = _lexical_hits(db, question)
    snippets = []
    for paper in hits:
        bit = (paper.abstract or paper.why_it_matters or "")[:400]
        snippets.append(f"{paper.title} ({paper.year or 'n.d.'})\n{bit}")
    lexical = "\n\n".join(snippets)

    if not settings.has_openai:
        extra = "Closest metadata matches:\n\n" + lexical if lexical else "No keyword matches in the local corpus yet."
        return _degraded(
            question,
            "Set OPENAI_API_KEY in `.env` to enable FutureHouse PaperQA2 over OA full text.",
            extra,
        )

    if not pdfs:
        extra = "Closest metadata matches:\n\n" + lexical if lexical else ""
        return _degraded(
            question,
            "No open-access PDFs are stored yet. Run ingest; paywalled papers stay metadata-only.",
            extra,
        )

    try:
        from paperqa import Settings as PaperQASettings
        from paperqa import ask
    except ImportError:
        extra = "Closest metadata matches:\n\n" + lexical if lexical else ""
        return _degraded(
            question,
            "Install PaperQA2 with `pip install -e '.[qa]'` after the OpenAI key is available.",
            extra,
        )

    pqa_settings = PaperQASettings(
        llm=settings.openai_model,
        summary_llm=settings.openai_model,
        temperature=0.1,
        paper_directory=str(settings.pdf_dir),
        agent={
            "index": {
                "paper_directory": str(settings.pdf_dir),
                "index_directory": str(settings.index_dir),
            }
        },
    )
    result = ask(question, settings=pqa_settings)
    answer = getattr(result, "formatted_answer", None) or getattr(result, "answer", None) or str(result)
    context = getattr(result, "context", None)
    session = getattr(result, "session", None)
    if session is not None and not answer:
        answer = getattr(session, "formatted_answer", None) or getattr(session, "answer", str(session))
        context = getattr(session, "context", context)
    return {
        "question": question,
        "answer": answer,
        "context": context,
        "mode": "paperqa2",
        "degraded": False,
        "detail": None,
    }
