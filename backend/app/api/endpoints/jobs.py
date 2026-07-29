import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException, Response
from typing import List
from backend.app.db.models import JobModel, JobCreateRequest, IncidentModel
from backend.app.db.repository import SQLiteScanRepository
from backend.app.queue.worker import JobWorker
from backend.app.core.exporters import Exporters

router = APIRouter()
repo = SQLiteScanRepository()
worker = JobWorker()

@router.post("/jobs", response_model=JobModel)
async def create_job(req: JobCreateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    job = JobModel(
        id=job_id,
        target_path=req.target_path,
        status="PENDING"
    )
    repo.create_job(job)

    # Launch background worker task
    background_tasks.add_task(worker.execute_job, job_id, req.run_ai_enrichment)
    return job

@router.get("/jobs", response_model=List[JobModel])
async def list_jobs():
    return repo.list_jobs(limit=50)

@router.get("/jobs/{job_id}", response_model=JobModel)
async def get_job(job_id: str):
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return job

@router.get("/jobs/{job_id}/incidents", response_model=List[IncidentModel])
async def get_job_incidents(job_id: str):
    return repo.get_job_incidents(job_id)

@router.get("/jobs/{job_id}/export/{format}")
async def export_job(job_id: str, format: str):
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    incidents = repo.get_job_incidents(job_id)

    fmt = format.lower()
    if fmt == "json":
        content = Exporters.to_json(job, incidents)
        return Response(content=content, media_type="application/json")
    elif fmt == "csv":
        content = Exporters.to_csv(incidents)
        return Response(content=content, media_type="text/csv")
    elif fmt == "sarif":
        content = Exporters.to_sarif(job, incidents)
        return Response(content=content, media_type="application/json")
    elif fmt == "markdown" or fmt == "md":
        content = Exporters.to_markdown(job, incidents)
        return Response(content=content, media_type="text/markdown")
    else:
        raise HTTPException(status_code=400, detail="Formato não suportado. Use json, csv, sarif ou markdown.")
