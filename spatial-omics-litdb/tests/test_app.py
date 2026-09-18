def test_empty_dashboard(empty_client):
    response = empty_client.get("/")
    assert response.status_code == 200
    assert 'id="empty-state"' in response.text
    assert "No papers in the local corpus yet" in response.text
    stats = empty_client.get("/api/stats").json()
    assert stats["total"] == 0
    assert stats["openai_configured"] is False


def test_seeded_search_and_filters(seeded_client):
    listing = seeded_client.get("/api/papers").json()
    assert listing["total"] >= 8
    visium = seeded_client.get("/api/papers", params={"q": "Visium HD"}).json()
    assert visium["total"] >= 1
    assert any("Visium" in (p.get("platforms") or []) or "Visium HD" in (p.get("platforms") or []) for p in visium["papers"])

    proteomics = seeded_client.get("/api/papers", params={"modality": "proteomics"}).json()
    assert proteomics["total"] >= 1
    assert all(p["modality"] == "proteomics" for p in proteomics["papers"])

    needed = seeded_client.get("/api/papers", params={"access": "needed"}).json()
    assert needed["total"] >= 1
    assert all(p["access_needed"] for p in needed["papers"])

    preprints = seeded_client.get("/api/papers", params={"record_type": "preprint"}).json()
    assert preprints["total"] >= 1
    assert all(p["is_preprint"] for p in preprints["papers"])

    imc = seeded_client.get("/api/papers", params={"platform": "IMC"}).json()
    assert imc["total"] >= 1

    html = seeded_client.get("/", params={"q": "Visium"}).text
    assert "High-definition spatial transcriptomic" in html
    assert 'id="empty-state"' not in html

    empty_filters = seeded_client.get("/", params={"q": "this-should-match-nothing-xyz"}).text
    assert 'id="empty-filters"' in empty_filters

    paper_id = visium["papers"][0]["id"]
    page = seeded_client.get(f"/papers/{paper_id}")
    assert page.status_code == 200
    assert "Why it matters for a new project" in page.text
    assert "Impactful experiments" in page.text


def test_qa_degrades_without_openai(seeded_client):
    html = seeded_client.get("/ask").text
    assert 'id="qa-degraded"' in html
    posted = seeded_client.post("/ask", data={"question": "Which papers use Visium HD?"})
    assert posted.status_code == 200
    assert "PaperQA2 is not running yet" in posted.text
    api = seeded_client.post("/api/ask", json={"question": "Which papers use Visium HD?"}).json()
    assert api["degraded"] is True
    assert api["mode"] == "degraded"
