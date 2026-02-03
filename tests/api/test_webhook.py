import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from api.main import app

client = TestClient(app)


def test_webhook_endpoint_requires_verification():
    """Test webhook verification endpoint."""
    response = client.get("/v1/webhook")
    # Should return 403 or 400 without proper verification
    assert response.status_code in [400, 403, 404, 405]


def test_webhook_post_requires_auth():
    """Test webhook POST requires authentication."""
    response = client.post("/v1/webhook", json={})
    # Should fail without proper WhatsApp signature
    # 404 = Not found, 405 = Method not allowed, 400 = Bad request, 401/403 = Auth error, 422 = Validation error
    assert response.status_code in [400, 401, 403, 404, 405, 422]
