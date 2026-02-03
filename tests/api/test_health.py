import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_metrics_endpoint():
    """Test the metrics endpoint."""
    response = client.get("/v1/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


def test_root_endpoint():
    """Test the root endpoint redirects or returns 404."""
    response = client.get("/")
    # Root endpoint may not exist, which is fine
    assert response.status_code in [200, 404]
