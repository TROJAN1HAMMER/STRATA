import json
import os
from typing import Any, Dict, Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.app.core.config import get_settings
from backend.app.db.database import Base, get_db
from backend.app.main import app

# In-memory SQLite database dedicated for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    future=True,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def synthetic_benchmark_data() -> Dict[str, Any]:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    benchmark_file = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "synthetic", "sample_observation.json"))
    if os.path.exists(benchmark_file):
        with open(benchmark_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "infrastructure": {
            "name": "Fallback Test Bridge",
            "structure_type": "BRIDGE",
            "latitude": 45.123,
            "longitude": -73.456,
            "description": "Fallback synthetic bridge target",
        },
        "observations": [
            {
                "acquisition_timestamp": "2026-01-01T00:00:00Z",
                "deformation_mm": -1.5,
                "velocity_mm_per_year": -4.0,
                "coherence": 0.85,
                "phase_quality": 0.90,
                "incidence_angle": 35.0,
                "los_displacement_mm": -1.2,
                "source": "SYNTHETIC",
            }
        ],
    }
