from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from spatial_omics_litdb.config import Settings
from spatial_omics_litdb.db import init_db, make_engine, session_factory
from spatial_omics_litdb.main import create_app
from spatial_omics_litdb.seed import seed_demo


@pytest.fixture
def tmp_settings(tmp_path: Path) -> Settings:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'litdb.sqlite3'}",
        data_dir=tmp_path,
        openai_api_key=None,
        contact_email="lab@example.com",
    )
    settings.ensure_dirs()
    return settings


@pytest.fixture
def empty_client(tmp_settings: Settings) -> TestClient:
    app = create_app(tmp_settings)
    return TestClient(app)


@pytest.fixture
def seeded_client(tmp_settings: Settings) -> TestClient:
    engine = make_engine(tmp_settings)
    init_db(engine)
    db = session_factory(engine)()
    seed_demo(db)
    db.close()
    return TestClient(create_app(tmp_settings))
