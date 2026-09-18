from spatial_omics_litdb.classify import classify, in_scope


def test_visium_hd_crc():
    tagged = classify(
        "High-definition spatial transcriptomic profiling of immune cell populations in colorectal cancer",
        "Here, we introduce the high-definition Visium spatial transcriptomic technology (Visium HD) and investigate human CRC samples with single-cell-scale resolution.",
    )
    assert tagged.modality == "transcriptomics"
    assert "Visium HD" in tagged.platforms
    assert tagged.resolution == "single-cell"
    assert tagged.organism == "human"
    assert tagged.tissue in {"colon", "tumor"}


def test_merfish_subcellular():
    tagged = classify(
        "Highly multiplexed spatial transcriptomics in bacteria",
        "We combined volumetric expansion with multiplexed error-robust fluorescence in situ hybridization (MERFISH) inside Escherichia coli.",
    )
    assert tagged.modality == "transcriptomics"
    assert "MERFISH" in tagged.platforms
    assert tagged.resolution == "subcellular"
    assert tagged.organism == "bacteria"


def test_spatial_proteomics_review():
    tagged = classify(
        "Spatial proteomics in translational and clinical research",
        "This review discusses CODEX, imaging mass cytometry, MIBI, and deep visual proteomics.",
    )
    assert tagged.modality == "proteomics"
    assert tagged.study_type == "review"
    assert "CODEX" in tagged.platforms
    assert "IMC" in tagged.platforms


def test_multiomics_and_out_of_scope():
    tagged = classify(
        "Spatial multi-omics profiling of breast cancer oligo-recurrent lung metastasis",
        "Combining spatial transcriptomics and spatial proteomics in human breast tumors.",
    )
    assert tagged.modality == "multi-omics"
    assert in_scope("Visium atlas of mouse brain", "spatial transcriptomics")
    assert not in_scope("A recipe for sourdough bread", "flour and water")
