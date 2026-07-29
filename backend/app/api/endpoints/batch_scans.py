import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List
from backend.app.db.models import BatchScanRequest, BatchScanModel, BatchScanJobModel
from backend.app.db.repository import SQLiteScanRepository
from backend.app.integrations.indexer_client import IndexerClient
from backend.app.queue.batch_worker import process_batch_scan

router = APIRouter()
repo = SQLiteScanRepository()


@router.post("/scan-indexed", response_model=BatchScanModel, status_code=202)
async def scan_indexed_repositories(req: BatchScanRequest, background_tasks: BackgroundTasks):
    """
    Consulta o GitRepository Intelligence Indexer com os filtros fornecidos,
    e enfileira escaneamento de segurança para cada repositório encontrado.
    """
    client = IndexerClient()

    # 1. Verificar se o Indexer está disponível
    if not await client.health_check():
        raise HTTPException(
            status_code=503,
            detail="GitRepository Intelligence Indexer não está disponível em http://localhost:8000. Inicie o Indexer primeiro."
        )

    # 2. Consultar repositórios no Indexer
    try:
        repositories = await client.fetch_repositories(
            tag=req.tag,
            dependency=req.dependency,
            language=req.language,
            stars_min=req.stars_min,
            score_min=req.score_min,
            limit=req.limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Erro ao consultar o Indexer: {str(e)}"
        )

    if not repositories:
        raise HTTPException(
            status_code=404,
            detail="Nenhum repositório encontrado no Indexer com os filtros fornecidos."
        )

    # 3. Montar descrição da query
    query_parts = []
    if req.tag:
        query_parts.append(f"tag={req.tag}")
    if req.dependency:
        query_parts.append(f"dependency={req.dependency}")
    if req.language:
        query_parts.append(f"language={req.language}")
    if req.score_min is not None:
        query_parts.append(f"score_min={req.score_min}")
    if req.stars_min is not None:
        query_parts.append(f"stars_min={req.stars_min}")
    source_query = ", ".join(query_parts) or "all"

    # 4. Criar batch scan
    batch_id = str(uuid.uuid4())[:8]
    batch = BatchScanModel(
        id=batch_id,
        source_query=source_query,
        status="PENDING",
        total_repos=len(repositories),
    )
    repo.create_batch_scan(batch)

    # 5. Enfileirar processamento em background
    background_tasks.add_task(
        process_batch_scan,
        batch_id=batch_id,
        repositories=repositories,
        run_ai=req.run_ai_enrichment,
    )

    return batch


@router.get("/batch-scans", response_model=List[BatchScanModel])
async def list_batch_scans():
    """Lista todos os escaneamentos em lote."""
    return repo.list_batch_scans(limit=50)


@router.get("/batch-scans/{batch_id}")
async def get_batch_scan_detail(batch_id: str):
    """Retorna detalhes do batch com status de cada repositório escaneado."""
    batch = repo.get_batch_scan(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch scan não encontrado.")

    batch_jobs = repo.get_batch_scan_jobs(batch_id)

    # Enriquecer com contadores de cada job
    repositories = []
    for bsj in batch_jobs:
        job = repo.get_job(bsj.job_id)
        repo_detail = {
            "name": bsj.repository_name,
            "url": bsj.repository_url,
            "scan_status": bsj.status,
            "job_id": bsj.job_id,
            "critical": job.critical_count if job else 0,
            "high": job.high_count if job else 0,
            "medium": job.medium_count if job else 0,
            "low": job.low_count if job else 0,
        }
        repositories.append(repo_detail)

    return {
        "batch_id": batch.id,
        "source_query": batch.source_query,
        "status": batch.status,
        "total_repos": batch.total_repos,
        "completed": batch.completed,
        "failed": batch.failed,
        "created_at": batch.created_at,
        "finished_at": batch.finished_at,
        "repositories": repositories,
    }
