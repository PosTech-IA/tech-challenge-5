import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Create test database BEFORE any imports
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def mock_init_db_func(config):
    """Mock function to initialize with test database"""
    import shared.database as db_module
    db_module.engine = test_engine
    db_module.SessionLocal = TestingSessionLocal
    return test_engine, TestingSessionLocal


def mock_init_storage(config):
    """Mock MinIO initialization"""
    pass


# Patch at module level before any app imports
pytest_plugins = []

# Apply patches globally for all tests
pytestmark = [
    pytest.mark.usefixtures("patch_db_init"),
]


@pytest.fixture(scope="session", autouse=True)
def patch_db_init():
    """Patch database and storage initialization before app imports"""
    with patch("shared.database.init_db", side_effect=mock_init_db_func):
        with patch("shared.storage.init_storage", side_effect=mock_init_storage):
            yield


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup and teardown test database for each test"""
    from shared.database import Base

    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Clean up
    Base.metadata.drop_all(bind=test_engine)
