"""
tests/test_api.py - Integration tests for the Resume Analyzer API.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def client():
    from backend.main import app
    from backend.utils.database import init_db
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_analyze_job(client):
    response = await client.post("/api/analyze_job", json={
        "job_role": "Python Developer",
        "job_description": "We need a Python developer with 3+ years of experience in FastAPI, PostgreSQL, and Docker. Strong knowledge of REST APIs required.",
    })
    assert response.status_code == 200
    data = response.json()
    assert "job_profile_id" in data
    assert isinstance(data["required_skills"], list)
    assert isinstance(data["keywords"], list)
    return data["job_profile_id"]


@pytest.mark.asyncio
async def test_upload_unsupported_type(client):
    """Should reject non-PDF/DOCX files."""
    from io import BytesIO
    fake_file = BytesIO(b"fake content")
    response = await client.post(
        "/api/upload_resume",
        files=[("files", ("resume.txt", fake_file, "text/plain"))],
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_rank_candidates_invalid_job(client):
    """Should return 404 for unknown job profile."""
    response = await client.post("/api/rank_candidates", json={
        "file_ids": ["some-file-id"],
        "job_profile_id": "non-existent-id",
    })
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_invalid_job(client):
    """Should return 404 for unknown job profile in export."""
    response = await client.get("/api/export_shortlist",
                                params={"job_profile_id": "bad-id", "format": "csv"})
    assert response.status_code == 404
