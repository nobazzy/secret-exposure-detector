import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import init_db
from backend.app.db.repository import SQLiteScanRepository

client = TestClient(app)
repo = SQLiteScanRepository()


def setup_module(module):
    init_db()


def test_scan_indexed_endpoint_indexer_unavailable():
    """Testa se o endpoint retorna 503 quando o Indexer não está rodando."""
    with patch("backend.app.integrations.indexer_client.IndexerClient.health_check", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = False

        response = client.post("/api/scan-indexed", json={"tag": "SaaS", "limit": 5})
        assert response.status_code == 503
        assert "não está disponível" in response.json()["detail"]


def test_scan_indexed_endpoint_no_repos_found():
    """Testa 404 quando o Indexer retorna lista vazia."""
    with patch("backend.app.integrations.indexer_client.IndexerClient.health_check", new_callable=AsyncMock) as mock_health, \
         patch("backend.app.integrations.indexer_client.IndexerClient.fetch_repositories", new_callable=AsyncMock) as mock_fetch:
        mock_health.return_value = True
        mock_fetch.return_value = []

        response = client.post("/api/scan-indexed", json={"tag": "NonExistentTag", "limit": 5})
        assert response.status_code == 404
        assert "Nenhum repositório encontrado" in response.json()["detail"]


def test_scan_indexed_success_flow():
    """Testa a criação de um batch scan com sucesso."""
    mock_repos = [
        {
            "name": "org/repo-a",
            "full_name": "org/repo-a",
            "url": "https://github.com/org/repo-a",
            "score": 90.0,
            "tags": ["saas", "stripe"],
        },
        {
            "name": "org/repo-b",
            "full_name": "org/repo-b",
            "url": "https://github.com/org/repo-b",
            "score": 85.0,
            "tags": ["saas", "nextjs"],
        },
    ]

    with patch("backend.app.integrations.indexer_client.IndexerClient.health_check", new_callable=AsyncMock) as mock_health, \
         patch("backend.app.integrations.indexer_client.IndexerClient.fetch_repositories", new_callable=AsyncMock) as mock_fetch, \
         patch("backend.app.api.endpoints.batch_scans.process_batch_scan", new_callable=AsyncMock) as mock_process:
        
        mock_health.return_value = True
        mock_fetch.return_value = mock_repos

        response = client.post(
            "/api/scan-indexed",
            json={
                "tag": "SaaS",
                "dependency": "stripe",
                "score_min": 80.0,
                "limit": 10
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert "id" in data
        assert data["status"] == "PENDING"
        assert data["total_repos"] == 2
        assert "tag=SaaS" in data["source_query"]

        batch_id = data["id"]

        # Verificar GET /api/batch-scans
        list_resp = client.get("/api/batch-scans")
        assert list_resp.status_code == 200
        batches = list_resp.json()
        assert any(b["id"] == batch_id for b in batches)

        # Verificar GET /api/batch-scans/{batch_id}
        detail_resp = client.get(f"/api/batch-scans/{batch_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["batch_id"] == batch_id
        assert detail["total_repos"] == 2
