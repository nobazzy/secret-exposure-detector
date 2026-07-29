import asyncio
import uuid
import logging
from datetime import datetime
from backend.app.db.models import JobModel, BatchScanModel, BatchScanJobModel
from backend.app.db.repository import SQLiteScanRepository
from backend.app.queue.worker import JobWorker

logger = logging.getLogger("batch_worker")

repo = SQLiteScanRepository()
worker = JobWorker()

CONCURRENCY_LIMIT = 5  # Processa até 5 repositórios em paralelo


async def process_batch_scan(
    batch_id: str,
    repositories: list[dict],
    run_ai: bool = False,
):
    """
    Processa um batch de repositórios vindos do Indexer em PARALELO (5 por vez).
    """
    batch = repo.get_batch_scan(batch_id)
    if not batch:
        logger.error(f"Batch {batch_id} não encontrado.")
        return

    batch.status = "RUNNING"
    repo.update_batch_scan(batch)

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def _scan_single_repo(repo_data: dict):
        async with semaphore:
            repo_url = repo_data.get("url", "")
            repo_name = repo_data.get("full_name", repo_url)
            job_id = str(uuid.uuid4())[:8]

            try:
                # 1. Criar job normal
                job = JobModel(
                    id=job_id,
                    target_path=repo_url,
                    status="PENDING",
                )
                repo.create_job(job)

                # 2. Registrar ligação batch ↔ job
                bsj = BatchScanJobModel(
                    batch_id=batch_id,
                    job_id=job_id,
                    repository_url=repo_url,
                    repository_name=repo_name,
                    status="RUNNING",
                )
                repo.add_batch_scan_job(bsj)

                # 3. Executar o pipeline de varredura
                await worker.execute_job(job_id, run_ai)

                # 4. Atualizar status do job no batch
                repo.update_batch_scan_job_status(job_id, "COMPLETED")
                batch.completed += 1

            except Exception as e:
                logger.error(f"Erro no scan do repo {repo_name}: {e}")
                repo.update_batch_scan_job_status(job_id, "FAILED")
                batch.failed += 1

            repo.update_batch_scan(batch)

    # Dispara os scans simultâneos com controle de concorrência
    tasks = [_scan_single_repo(r) for r in repositories]
    await asyncio.gather(*tasks, return_exceptions=True)

    # Finalizar batch
    batch.status = "COMPLETED"
    batch.finished_at = datetime.now().isoformat()
    repo.update_batch_scan(batch)
    logger.info(f"Batch {batch_id} finalizado: {batch.completed} ok, {batch.failed} falhas.")
