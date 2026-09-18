from __future__ import annotations

import re
from dataclasses import dataclass

from spatial_omics_litdb.taxonomy import SCOPE_KEYWORDS

PLATFORM_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Visium HD", re.compile(r"\bvisium[\s-]*hd\b", re.I)),
    ("Visium", re.compile(r"\bvisium\b", re.I)),
    ("Stereo-seq", re.compile(r"\bstereo[\s-]*seq\b", re.I)),
    ("MERFISH", re.compile(r"\bmerfish\b", re.I)),
    ("MERSCOPE", re.compile(r"\bmerscope\b", re.I)),
    ("CosMx", re.compile(r"\bcosmx\b", re.I)),
    ("Xenium", re.compile(r"\bxenium\b", re.I)),
    ("PhenoCycler", re.compile(r"\bphenocycler\b", re.I)),
    ("CODEX", re.compile(r"\bcodex\b", re.I)),
    ("IMC", re.compile(r"\b(?:imaging mass cytometry|\bimc\b|hyperion)\b", re.I)),
    ("MIBI", re.compile(r"\bmibi(?:-tof)?\b", re.I)),
    ("Slide-seq", re.compile(r"\bslide[\s-]*seq(?:[\s-]*v2)?\b", re.I)),
    ("seqFISH", re.compile(r"\bseqfish(?:\+)?\b", re.I)),
    ("GeoMx", re.compile(r"\bgeomx\b|\bdsp\b", re.I)),
    ("DBiT-seq", re.compile(r"\bdbit[\s-]*seq\b", re.I)),
    ("MALDI-MSI", re.compile(r"\bmaldi(?:-msi)?\b|\bmaldi imaging\b", re.I)),
    ("Deep Visual Proteomics", re.compile(r"\bdeep visual proteomics\b|\bdvp\b", re.I)),
    ("STARmap", re.compile(r"\bstarmap\b", re.I)),
    ("osmFISH", re.compile(r"\bosmfish\b", re.I)),
]

TRANSCRIPTOMICS_RE = re.compile(
    r"spatial transcriptom|spatially resolved transcriptom|in situ hybridiz|"
    r"in situ sequencing|spatial gene expression|visium|xenium|cosmx|"
    r"merfish|seqfish|stereo[\s-]*seq|slide[\s-]*seq|geomx",
    re.I,
)
PROTEOMICS_RE = re.compile(
    r"spatial proteom|spatially resolved proteom|codex|phenocycler|"
    r"imaging mass cytometry|\bimc\b|mibi|maldi|deep visual proteomics|"
    r"antibody[- ]based spatial|cyclic immunofluorescence",
    re.I,
)

SPOT_PLATFORMS = {"Visium", "Slide-seq", "GeoMx", "DBiT-seq"}
SUBCELLULAR_PLATFORMS = {
    "MERFISH",
    "seqFISH",
    "osmFISH",
    "STARmap",
    "Xenium",
    "CosMx",
    "MERSCOPE",
}
SINGLE_CELL_PLATFORMS = {
    "Visium HD",
    "Stereo-seq",
    "CODEX",
    "PhenoCycler",
    "IMC",
    "MIBI",
    "Xenium",
    "CosMx",
    "MERFISH",
    "Deep Visual Proteomics",
}

ORGANISM_PATTERNS = [
    ("human", re.compile(r"\b(?:human|patient|homo sapiens)\b", re.I)),
    ("mouse", re.compile(r"\b(?:mouse|mice|murine|mus musculus)\b", re.I)),
    ("rat", re.compile(r"\b(?:rat|rattus)\b", re.I)),
    ("zebrafish", re.compile(r"\b(?:zebrafish|danio)\b", re.I)),
    ("drosophila", re.compile(r"\b(?:drosophila|fruit fly)\b", re.I)),
    ("organoid", re.compile(r"\borganoids?\b", re.I)),
    ("bacteria", re.compile(r"\b(?:bacteri(?:a|al|um)|e\.?\s*coli)\b", re.I)),
]

TISSUE_PATTERNS = [
    ("brain", re.compile(r"\b(?:brain|cortex|hippocamp|neuron)\b", re.I)),
    ("lung", re.compile(r"\b(?:lung|pulmonary|alveol)\b", re.I)),
    ("colon", re.compile(r"\b(?:colon|colorectal|intestine|gut)\b", re.I)),
    ("breast", re.compile(r"\b(?:breast|mammary)\b", re.I)),
    ("liver", re.compile(r"\b(?:liver|hepatic)\b", re.I)),
    ("kidney", re.compile(r"\b(?:kidney|renal)\b", re.I)),
    ("heart", re.compile(r"\b(?:heart|cardiac)\b", re.I)),
    ("tumor", re.compile(r"\b(?:tumor|tumour|cancer|carcinoma|tme)\b", re.I)),
    ("skin", re.compile(r"\b(?:skin|dermis|epiderm)\b", re.I)),
    ("lymph node", re.compile(r"\blymph node", re.I)),
]

DISEASE_PATTERNS = [
    ("cancer", re.compile(r"\b(?:cancer|carcinoma|tumor|tumour|oncolog|metastas)\b", re.I)),
    ("fibrosis", re.compile(r"\bfibrosis\b", re.I)),
    ("neurodegeneration", re.compile(r"\b(?:alzheimer|parkinson|neurodegener)\b", re.I)),
    ("inflammation", re.compile(r"\b(?:inflamm|immune|autoimmun)\b", re.I)),
    ("infection", re.compile(r"\b(?:infect|pathogen|virus|bacterial)\b", re.I)),
]


@dataclass
class Classification:
    modality: str
    platforms: list[str]
    resolution: str
    organism: str | None
    tissue: str | None
    disease_or_system: str | None
    study_type: str
    data_availability: str | None
    code_availability: str | None
    impactful_experiments: str
    novel_approaches: str
    why_it_matters: str


def in_scope(title: str, abstract: str | None) -> bool:
    blob = f"{title} {abstract or ''}".lower()
    return any(term in blob for term in SCOPE_KEYWORDS)


def _first_match(blob: str, patterns: list[tuple[str, re.Pattern[str]]]) -> str | None:
    for label, pattern in patterns:
        if pattern.search(blob):
            return label
    return None


def _platforms(blob: str) -> list[str]:
    found: list[str] = []
    for label, pattern in PLATFORM_PATTERNS:
        if pattern.search(blob) and label not in found:
            found.append(label)
    if "Visium HD" in found:
        found = [p for p in found if p != "Visium"]
    if "PhenoCycler" in found:
        found = [p for p in found if p != "CODEX"]
    return found


def _modality(blob: str, platforms: list[str]) -> str:
    tx = bool(TRANSCRIPTOMICS_RE.search(blob)) or any(
        p in platforms
        for p in (
            "Visium",
            "Visium HD",
            "Stereo-seq",
            "MERFISH",
            "MERSCOPE",
            "CosMx",
            "Xenium",
            "Slide-seq",
            "seqFISH",
            "GeoMx",
            "DBiT-seq",
            "STARmap",
            "osmFISH",
        )
    )
    px = bool(PROTEOMICS_RE.search(blob)) or any(
        p in platforms
        for p in (
            "CODEX",
            "PhenoCycler",
            "IMC",
            "MIBI",
            "MALDI-MSI",
            "Deep Visual Proteomics",
        )
    )
    if tx and px:
        return "multi-omics"
    if tx:
        return "transcriptomics"
    if px:
        return "proteomics"
    if "spatial multi" in blob:
        return "multi-omics"
    return "unknown"


def _resolution(blob: str, platforms: list[str]) -> str:
    if re.search(r"\bsubcellular\b|\bnanometer\b|\bexpansion microscopy\b", blob):
        return "subcellular"
    if re.search(r"\bsingle[\s-]*cell\b|\bcell[\s-]*scale\b|\bcell[\s-]*level\b", blob):
        if any(p in SUBCELLULAR_PLATFORMS for p in platforms):
            return "subcellular"
        return "single-cell"
    if re.search(r"\bspot\b|\bspot[\s-]*level\b|\bcapture area\b", blob):
        return "spot"
    if any(p in SUBCELLULAR_PLATFORMS for p in platforms):
        return "subcellular"
    if any(p in SINGLE_CELL_PLATFORMS for p in platforms):
        return "single-cell"
    if any(p in SPOT_PLATFORMS for p in platforms):
        return "spot"
    return "unknown"


def _study_type(title: str, blob: str) -> str:
    if re.search(r"\b(review|perspective|primer|survey|commentary)\b", title, re.I):
        return "review"
    if re.search(r"\b(review|we review|this review)\b", blob):
        return "review"
    if re.search(r"\b(atlas|landscape|cell map|tissue map)\b", blob):
        return "atlas"
    if re.search(
        r"\b(computational|algorithm|software|pipeline|foundation model|"
        r"machine learning|deep learning|benchmark)\b",
        blob,
    ):
        return "computational"
    if re.search(
        r"\b(patient|clinical|trial|prognos|diagnos|immunotherapy|cohort)\b", blob
    ):
        return "clinical"
    if re.search(
        r"\b(method|protocol|assay|platform|technology|we (?:introduce|present|develop))\b",
        blob,
    ):
        return "methods"
    return "unknown"


def _availability(blob: str, kind: str) -> str | None:
    if kind == "data":
        if re.search(
            r"\b(geo|ega|pride|massive|zenodo|figshare|dbgap|processed data|"
            r"data availability|deposited)\b",
            blob,
        ):
            return "Mentioned in abstract — confirm in paper"
        return None
    if re.search(r"\b(github|gitlab|zenodo|code availability|open[- ]source)\b", blob):
        return "Mentioned in abstract — confirm in paper"
    return None


def _sentences(text: str, n: int = 2) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(p.strip() for p in parts[:n] if p.strip())


def classify(title: str, abstract: str | None, extra: str | None = None) -> Classification:
    blob = f"{title} {abstract or ''} {extra or ''}"
    platforms = _platforms(blob)
    modality = _modality(blob, platforms)
    resolution = _resolution(blob, platforms)
    organism = _first_match(blob, ORGANISM_PATTERNS)
    tissue = _first_match(blob, TISSUE_PATTERNS)
    disease = _first_match(blob, DISEASE_PATTERNS)
    study_type = _study_type(title, blob.lower())
    experiments = _sentences(abstract or title, 2)
    novel = ", ".join(platforms) if platforms else "Not named in title/abstract"
    if study_type == "methods":
        why = "Methods paper — candidate to adopt, benchmark, or combine with an existing lab assay."
    elif study_type == "atlas":
        why = "Atlas-scale map — useful as a reference or to spot under-profiled niches."
    elif study_type == "computational":
        why = "Computational method — may be reusable on in-house spatial datasets."
    elif study_type == "clinical":
        why = "Clinical or patient study — possible translational angle or cohort design to emulate."
    elif study_type == "review":
        why = "Review — fast way to scan the 2025+ landscape before designing a project."
    else:
        why = "Recent spatial omics report — check platform and system overlap with lab interests."
    if modality == "multi-omics":
        why += " Joint transcriptomic/proteomic angle may seed a combined experiment."
    return Classification(
        modality=modality,
        platforms=platforms,
        resolution=resolution,
        organism=organism,
        tissue=tissue,
        disease_or_system=disease,
        study_type=study_type,
        data_availability=_availability(blob, "data"),
        code_availability=_availability(blob, "code"),
        impactful_experiments=experiments,
        novel_approaches=novel,
        why_it_matters=why,
    )
