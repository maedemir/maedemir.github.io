from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from spatial_omics_litdb.classify import classify
from spatial_omics_litdb.ingest import make_uid, normalize_doi
from spatial_omics_litdb.ingest.pipeline import _search_text
from spatial_omics_litdb.models import Paper

# Public bibliographic metadata from OpenAlex / publisher pages (2025+).
# Used so the dashboard can be reviewed without API keys or live ingest.
DEMO_PAPERS = [
    {
        "doi": "10.1038/s41588-025-02193-3",
        "title": "High-definition spatial transcriptomic profiling of immune cell populations in colorectal cancer",
        "abstract": "A comprehensive understanding of cellular behavior and response to the tumor microenvironment (TME) in colorectal cancer (CRC) remains elusive. Here, we introduce the high-definition Visium spatial transcriptomic technology (Visium HD) and investigate formalin-fixed paraffin-embedded human CRC samples (n = 5). We demonstrate the high sensitivity, single-cell-scale resolution and spatial accuracy of Visium HD, generating a highly refined whole-transcriptome spatial profile of CRC samples.",
        "authors": ["Michelli F. Oliveira", "Juan P. Romero", "Meii Chung", "Stephen R. Williams"],
        "venue": "Nature Genetics",
        "year": 2025,
        "published_date": date(2025, 6, 1),
        "is_preprint": False,
        "record_type": "journal",
        "is_oa": True,
        "oa_status": "hybrid",
        "pdf_url": "https://doi.org/10.1038/s41588-025-02193-3",
        "landing_url": "https://doi.org/10.1038/s41588-025-02193-3",
        "sources": ["seed", "openalex"],
    },
    {
        "doi": "10.1126/science.adr0932",
        "title": "Highly multiplexed spatial transcriptomics in bacteria",
        "abstract": "To overcome the massive density of bacterial messenger RNA, we combined 1000-fold volumetric expansion with multiplexed error-robust fluorescence in situ hybridization (MERFISH) to create bacterial-MERFISH. This method enables high-throughput, spatially resolved profiling of thousands of operons within individual bacteria, including Escherichia coli and Bacteroides thetaiotaomicron in the mammalian colon.",
        "authors": ["Ari Sarfatis", "Yuanyou Wang", "Nana Twumasi-Ankrah", "Jeffrey R. Moffitt"],
        "venue": "Science",
        "year": 2025,
        "published_date": date(2025, 1, 23),
        "is_preprint": False,
        "record_type": "journal",
        "is_oa": True,
        "oa_status": "green",
        "pdf_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC12278067/pdf/nihms-2093853.pdf",
        "landing_url": "https://doi.org/10.1126/science.adr0932",
        "sources": ["seed", "openalex"],
    },
    {
        "doi": "10.1038/s41588-025-02080-x",
        "title": "Spatial transcriptomics identifies molecular niche dysregulation associated with distal lung remodeling in pulmonary fibrosis",
        "abstract": "Using image-based spatial transcriptomics, we analyzed the gene expression of 1.6 million cells from 35 unique lungs. We characterized PF-emergent cell types, established the cellular and molecular basis of classical histopathologic features, and identified distinct molecularly defined spatial niches in control and pulmonary fibrosis lungs.",
        "authors": ["Annika Vannan", "Ruqian Lyu", "Arianna L. Williams-Katek"],
        "venue": "Nature Genetics",
        "year": 2025,
        "published_date": date(2025, 2, 3),
        "is_preprint": False,
        "record_type": "journal",
        "is_oa": True,
        "oa_status": "hybrid",
        "landing_url": "https://doi.org/10.1038/s41588-025-02080-x",
        "sources": ["seed", "openalex"],
    },
    {
        "doi": "10.1038/s41592-025-02707-1",
        "title": "A visual–omics foundation model to bridge histopathology with spatial transcriptomics",
        "abstract": "We developed OmiCLIP, a visual-omics foundation model linking hematoxylin and eosin images and transcriptomics using tissue patches from Visium data. Building on OmiCLIP, the Loki platform offers tissue alignment, annotation, cell-type decomposition, and spatial transcriptomics gene expression prediction from H&E-stained images.",
        "authors": ["Weiqing Chen", "Pengzhi Zhang", "Tu Tran"],
        "venue": "Nature Methods",
        "year": 2025,
        "published_date": date(2025, 5, 29),
        "is_preprint": False,
        "record_type": "journal",
        "is_oa": True,
        "oa_status": "hybrid",
        "landing_url": "https://doi.org/10.1038/s41592-025-02707-1",
        "sources": ["seed", "openalex"],
    },
    {
        "doi": "10.1038/s44320-025-00101-9",
        "title": "Spatial proteomics in translational and clinical research",
        "abstract": "This review discusses recent advances in targeted and untargeted spatial proteomics, including CODEX, imaging mass cytometry, MIBI, and deep visual proteomics, and highlights their translational potential for tissue profiling in clinical research.",
        "authors": ["Péter Horváth", "Fabian Coscia"],
        "venue": "Molecular Systems Biology",
        "year": 2025,
        "published_date": date(2025, 4, 14),
        "is_preprint": False,
        "record_type": "journal",
        "is_oa": True,
        "oa_status": "gold",
        "landing_url": "https://doi.org/10.1038/s44320-025-00101-9",
        "sources": ["seed", "openalex"],
    },
    {
        "doi": "10.1101/2025.02.05.636714",
        "title": "scGPT-spatial: Continual Pretraining of Single-Cell Foundation Model for Spatial Transcriptomics",
        "abstract": "We present scGPT-spatial, a continual pretraining of a single-cell foundation model adapted to spatial transcriptomics. The computational method aims to transfer single-cell representations to spatially resolved gene expression, including Visium and imaging-based platforms, and is released as a preprint on bioRxiv.",
        "authors": ["scGPT-spatial authors"],
        "venue": "bioRxiv",
        "year": 2025,
        "published_date": date(2025, 2, 8),
        "is_preprint": True,
        "record_type": "preprint",
        "is_oa": True,
        "oa_status": "green",
        "pdf_url": "https://www.biorxiv.org/content/10.1101/2025.02.05.636714v1.full.pdf",
        "landing_url": "https://doi.org/10.1101/2025.02.05.636714",
        "sources": ["seed", "biorxiv"],
    },
    {
        "doi": "10.1101/2025.01.20.634005",
        "title": "ResolVI - addressing noise and bias in spatial transcriptomics",
        "abstract": "ResolVI is a computational method for addressing noise and bias in spatial transcriptomics datasets. We benchmark the approach on Visium and imaging-based spatial transcriptomics and provide code for reproducing the analyses.",
        "authors": ["ResolVI authors"],
        "venue": "bioRxiv",
        "year": 2025,
        "published_date": date(2025, 1, 24),
        "is_preprint": True,
        "record_type": "preprint",
        "is_oa": True,
        "oa_status": "green",
        "pdf_url": "https://www.biorxiv.org/content/10.1101/2025.01.20.634005v1.full.pdf",
        "landing_url": "https://www.biorxiv.org/content/10.1101/2025.01.20.634005",
        "sources": ["seed", "biorxiv"],
        "code_hint": True,
    },
    {
        "doi": "10.1016/j.ejso.2025.110587",
        "title": "Dissecting the tumor microenvironment in colorectal peritoneal metastases using spatial proteomics (IMC Hyperion)",
        "abstract": "We used imaging mass cytometry (IMC Hyperion) to dissect the tumor microenvironment in colorectal peritoneal metastases. Spatial proteomics revealed distinct immune niches. Full text is paywalled; metadata is retained so the lab can request access separately.",
        "authors": ["European Journal of Surgical Oncology authors"],
        "venue": "European Journal of Surgical Oncology",
        "year": 2025,
        "published_date": date(2025, 12, 1),
        "is_preprint": False,
        "record_type": "journal",
        "is_oa": False,
        "oa_status": "closed",
        "landing_url": "https://doi.org/10.1016/j.ejso.2025.110587",
        "sources": ["seed", "openalex"],
    },
    {
        "doi": "10.1038/s41388-025-03388-y",
        "title": "Spatial multi-omics profiling of breast cancer oligo-recurrent lung metastasis",
        "abstract": "Spatial multi-omics profiling of breast cancer oligo-recurrent lung metastasis combining spatial transcriptomics and spatial proteomics. The publisher version is closed access; this record is metadata-only with access needed.",
        "authors": ["Oncogene authors"],
        "venue": "Oncogene",
        "year": 2025,
        "published_date": date(2025, 4, 15),
        "is_preprint": False,
        "record_type": "journal",
        "is_oa": False,
        "oa_status": "closed",
        "landing_url": "https://doi.org/10.1038/s41388-025-03388-y",
        "sources": ["seed", "openalex"],
    },
    {
        "doi": "10.1016/j.cell.2025.08.039",
        "title": "Intrinsic heterogeneity of primary cilia revealed through spatial proteomics",
        "abstract": "Primary cilia are critical organelles found on most human cells. Using spatial proteomics we reveal intrinsic heterogeneity of primary cilia protein composition across cell types, with implications for ciliopathy biology.",
        "authors": ["Jan N. Hansen", "Huangqingbo Sun", "Konstantin Kahnert"],
        "venue": "Cell",
        "year": 2025,
        "published_date": date(2025, 9, 26),
        "is_preprint": False,
        "record_type": "journal",
        "is_oa": True,
        "oa_status": "hybrid",
        "landing_url": "https://doi.org/10.1016/j.cell.2025.08.039",
        "sources": ["seed", "openalex"],
    },
]


def seed_demo(db: Session, reset: bool = False) -> int:
    if reset:
        db.query(Paper).delete()
        db.commit()
    count = 0
    for item in DEMO_PAPERS:
        doi = normalize_doi(item["doi"])
        uid = make_uid(doi, "seed", doi, item["title"])
        existing = db.query(Paper).filter(Paper.uid == uid).one_or_none()
        paper = existing or Paper(uid=uid, title=item["title"])
        paper.doi = doi
        paper.title = item["title"]
        paper.abstract = item["abstract"]
        paper.authors = item["authors"]
        paper.venue = item["venue"]
        paper.year = item["year"]
        paper.published_date = item["published_date"]
        paper.is_preprint = item["is_preprint"]
        paper.record_type = item["record_type"]
        paper.is_oa = item["is_oa"]
        paper.oa_status = item["oa_status"]
        paper.pdf_url = item.get("pdf_url") if item["is_oa"] else None
        paper.landing_url = item["landing_url"]
        paper.access_needed = not item["is_oa"]
        paper.full_text_available = False
        paper.sources = item["sources"]
        tagged = classify(paper.title, paper.abstract)
        paper.modality = tagged.modality
        paper.platforms = tagged.platforms
        paper.resolution = tagged.resolution
        paper.organism = tagged.organism
        paper.tissue = tagged.tissue
        paper.disease_or_system = tagged.disease_or_system
        paper.study_type = tagged.study_type
        paper.data_availability = tagged.data_availability
        paper.code_availability = tagged.code_availability
        paper.impactful_experiments = tagged.impactful_experiments
        paper.novel_approaches = tagged.novel_approaches
        paper.why_it_matters = tagged.why_it_matters
        paper.search_text = _search_text(paper)
        if existing is None:
            db.add(paper)
        count += 1
    db.commit()
    return count
