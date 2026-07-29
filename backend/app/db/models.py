from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class IncidentModel(BaseModel):
    id: Optional[int] = None
    job_id: str
    file_path: str
    relative_path: str
    variable_name: str
    secret_value: Optional[str] = None
    line_number: int
    capability: str
    context_type: str
    risk_score: int
    criticality: str
    policy_overrides: Optional[List[str]] = []
    created_at: Optional[str] = None

class JobModel(BaseModel):
    id: str
    target_path: str
    status: str  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    total_files: int = 0
    analyzed_files: int = 0
    cached_files: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    duration_ms: float = 0.0
    throughput_files_per_sec: float = 0.0
    ai_summary: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

class JobCreateRequest(BaseModel):
    target_path: str
    run_ai_enrichment: bool = False


class BatchScanRequest(BaseModel):
    tag: Optional[str] = None
    dependency: Optional[str] = None
    language: Optional[str] = None
    score_min: Optional[float] = None
    stars_min: Optional[int] = None
    limit: int = 20
    run_ai_enrichment: bool = False


class BatchScanJobModel(BaseModel):
    id: Optional[int] = None
    batch_id: str
    job_id: str
    repository_url: str
    repository_name: str
    status: str = "PENDING"


class BatchScanModel(BaseModel):
    id: str
    source_query: str
    status: str = "PENDING"
    total_repos: int = 0
    completed: int = 0
    failed: int = 0
    created_at: Optional[str] = None
    finished_at: Optional[str] = None

