import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure test env vars
test_chroma_dir = os.path.join(tempfile.gettempdir(), "chroma_test_db")
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["MISTRAL_API_KEY"] = "mock_mistral_test_key"
os.environ["CHROMA_PERSIST_DIR"] = test_chroma_dir

from app.models.models import Base  # noqa: E402


@pytest.fixture(scope="function")
def in_memory_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
