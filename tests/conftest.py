"""Pytest configuration and fixtures for FastAPI tests."""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Fixture: Provide a TestClient instance for testing the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_email():
    """Fixture: Provide a sample email for testing."""
    return "test.student@mergington.edu"
