import httpx
from typing import Any, Dict, List, Optional


class IndexerClient:
    """
    Cliente HTTP que consulta a API do GitRepository Intelligence Indexer.
    Responsabilidade única: buscar repositórios indexados para análise de segurança.
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def health_check(self) -> bool:
        """Verifica se o Indexer está disponível."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False

    async def fetch_repositories(
        self,
        tag: Optional[str] = None,
        dependency: Optional[str] = None,
        language: Optional[str] = None,
        stars_min: Optional[int] = None,
        score_min: Optional[float] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Consulta GET /repositories do Indexer com filtros.
        Retorna lista de dicionários com url, full_name, score, etc.
        """
        params: Dict[str, Any] = {"limit": limit}
        if tag:
            params["tag"] = tag
        if dependency:
            params["dependency"] = dependency
        if language:
            params["language"] = language
        if stars_min is not None:
            params["stars_min"] = stars_min
        if score_min is not None:
            params["score_min"] = score_min

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/repositories",
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def search(self, q: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Consulta GET /search?q=... (FTS5 full-text search)."""
        params = {"q": q, "limit": limit}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
