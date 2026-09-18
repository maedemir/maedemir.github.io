from spatial_omics_litdb.ingest import make_uid, normalize_doi


def test_doi_normalization_and_uid():
    assert normalize_doi("https://doi.org/10.1038/s41588-025-02193-3") == "10.1038/s41588-025-02193-3"
    a = make_uid("10.1038/s41588-025-02193-3", "openalex", "W1", "Title")
    b = make_uid("https://doi.org/10.1038/s41588-025-02193-3", "pubmed", "123", "Other")
    assert a == b
    assert make_uid(None, "openalex", "W99", "Hello").startswith("openalex:")
