from abc import ABC, abstractmethod
from typing import List, Optional
import json
from datetime import datetime
from backend.app.db.database import get_connection
from backend.app.db.models import JobModel, IncidentModel, BatchScanModel, BatchScanJobModel

class AbstractScanRepository(ABC):
    @abstractmethod
    def create_job(self, job: JobModel) -> JobModel:
        pass

    @abstractmethod
    def update_job(self, job: JobModel) -> JobModel:
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[JobModel]:
        pass

    @abstractmethod
    def list_jobs(self, limit: int = 50) -> List[JobModel]:
        pass

    @abstractmethod
    def save_incident(self, incident: IncidentModel) -> IncidentModel:
        pass

    @abstractmethod
    def get_job_incidents(self, job_id: str) -> List[IncidentModel]:
        pass


class SQLiteScanRepository(AbstractScanRepository):
    def create_job(self, job: JobModel) -> JobModel:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO jobs (id, target_path, status, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (job.id, job.target_path, job.status),
        )
        conn.commit()
        conn.close()
        return job

    def update_job(self, job: JobModel) -> JobModel:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE jobs SET
                status = ?,
                total_files = ?,
                analyzed_files = ?,
                cached_files = ?,
                critical_count = ?,
                high_count = ?,
                medium_count = ?,
                low_count = ?,
                duration_ms = ?,
                throughput_files_per_sec = ?,
                ai_summary = ?,
                completed_at = ?
            WHERE id = ?
            """,
            (
                job.status,
                job.total_files,
                job.analyzed_files,
                job.cached_files,
                job.critical_count,
                job.high_count,
                job.medium_count,
                job.low_count,
                job.duration_ms,
                job.throughput_files_per_sec,
                job.ai_summary,
                job.completed_at,
                job.id,
            ),
        )
        conn.commit()
        conn.close()
        return job

    def get_job(self, job_id: str) -> Optional[JobModel]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return JobModel(**dict(row))

    def list_jobs(self, limit: int = 50) -> List[JobModel]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [JobModel(**dict(row)) for row in rows]

    def save_incident(self, incident: IncidentModel) -> IncidentModel:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO incidents (
                job_id, file_path, relative_path, variable_name, secret_value,
                line_number, capability, context_type, risk_score, criticality, policy_overrides
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident.job_id,
                incident.file_path,
                incident.relative_path,
                incident.variable_name,
                incident.secret_value,
                incident.line_number,
                incident.capability,
                incident.context_type,
                incident.risk_score,
                incident.criticality,
                json.dumps(incident.policy_overrides or []),
            ),
        )
        incident.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return incident

    def get_job_incidents(self, job_id: str) -> List[IncidentModel]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents WHERE job_id = ? ORDER BY risk_score DESC", (job_id,))
        rows = cursor.fetchall()
        conn.close()
        incidents = []
        for row in rows:
            data = dict(row)
            if data.get("policy_overrides"):
                try:
                    data["policy_overrides"] = json.loads(data["policy_overrides"])
                except Exception:
                    data["policy_overrides"] = []
            incidents.append(IncidentModel(**data))
        return incidents

    # ─── Batch Scan Methods ───

    def create_batch_scan(self, batch: BatchScanModel) -> BatchScanModel:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO batch_scans (id, source_query, status, total_repos, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (batch.id, batch.source_query, batch.status, batch.total_repos),
        )
        conn.commit()
        conn.close()
        return batch

    def update_batch_scan(self, batch: BatchScanModel) -> BatchScanModel:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE batch_scans SET
                status = ?,
                completed = ?,
                failed = ?,
                finished_at = ?
            WHERE id = ?
            """,
            (batch.status, batch.completed, batch.failed, batch.finished_at, batch.id),
        )
        conn.commit()
        conn.close()
        return batch

    def get_batch_scan(self, batch_id: str) -> Optional[BatchScanModel]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM batch_scans WHERE id = ?", (batch_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return BatchScanModel(**dict(row))

    def list_batch_scans(self, limit: int = 50) -> List[BatchScanModel]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM batch_scans ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [BatchScanModel(**dict(row)) for row in rows]

    def add_batch_scan_job(self, bsj: BatchScanJobModel) -> BatchScanJobModel:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO batch_scan_jobs (batch_id, job_id, repository_url, repository_name, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (bsj.batch_id, bsj.job_id, bsj.repository_url, bsj.repository_name, bsj.status),
        )
        bsj.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return bsj

    def update_batch_scan_job_status(self, job_id: str, status: str) -> None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE batch_scan_jobs SET status = ? WHERE job_id = ?",
            (status, job_id),
        )
        conn.commit()
        conn.close()

    def get_batch_scan_jobs(self, batch_id: str) -> List[BatchScanJobModel]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM batch_scan_jobs WHERE batch_id = ? ORDER BY id",
            (batch_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [BatchScanJobModel(**dict(row)) for row in rows]

