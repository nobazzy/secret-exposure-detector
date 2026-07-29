import time
from datetime import datetime
from pathlib import Path
from backend.app.db.models import JobModel, IncidentModel
from backend.app.db.repository import SQLiteScanRepository
from backend.app.core.discovery_wrapper import DiscoveryEngineWrapper
from backend.app.core.cache import CacheEngine
from backend.app.core.parser import ParserEngine
from backend.app.plugins.manager import PluginManager
from backend.app.core.incident_builder import IncidentBuilder
from backend.app.ai.ollama_client import OllamaClient
from backend.app.events.bus import bus, Event

class JobWorker:
    def __init__(self):
        self.repo = SQLiteScanRepository()
        self.plugin_manager = PluginManager()
        self.incident_builder = IncidentBuilder()
        self.ollama_client = OllamaClient()

    async def execute_job(self, job_id: str, run_ai: bool = False):
        job = self.repo.get_job(job_id)
        if not job:
            return

        job.status = "RUNNING"
        self.repo.update_job(job)

        start_time = time.time()

        # 1. Discovery (Supports both Local Folder Paths and Git HTTPS URLs)
        import asyncio
        discovery = DiscoveryEngineWrapper(job.target_path)
        files, root_path = await asyncio.to_thread(discovery.discover_files)

        job.total_files = len(files)
        self.repo.update_job(job)
        await bus.publish(Event("DiscoveryCompleted", {"job_id": job_id, "files": len(files)}))

        analyzed_count = 0
        cached_count = 0
        incidents_list = []

        try:
            # 2. Pipeline per file
            for file_path in files:
                await asyncio.sleep(0)  # Cede o event loop para o FastAPI responder requisições HTTP imediatamente
                current_hash = CacheEngine.calculate_sha256(file_path)

                if CacheEngine.is_cached(file_path, current_hash):
                    cached_count += 1
                    job.cached_files = cached_count

                    # Retrieve cached incidents and attach to this job
                    cached_incidents = CacheEngine.get_cached_incidents(file_path)
                    for cached_data in cached_incidents:
                        inc_model = IncidentModel(
                            job_id=job_id,
                            file_path=cached_data["file_path"],
                            relative_path=cached_data["relative_path"],
                            variable_name=cached_data["variable_name"],
                            secret_value=cached_data["secret_value"],
                            line_number=cached_data["line_number"],
                            capability=cached_data["capability"],
                            context_type=cached_data["context_type"],
                            risk_score=cached_data["risk_score"],
                            criticality=cached_data["criticality"],
                            policy_overrides=cached_data.get("policy_overrides", [])
                        )
                        self.repo.save_incident(inc_model)
                        incidents_list.append(inc_model)
                        self._update_job_counters(job, inc_model.criticality)

                    self.repo.update_job(job)
                    await bus.publish(Event("FileCacheHit", {"file": str(file_path)}))
                    continue

                # Parse
                parsed_file = ParserEngine.parse_file(file_path, root_path)
                analyzed_count += 1
                job.analyzed_files = analyzed_count

                # Detect
                raw_incidents = self.plugin_manager.run_detection(parsed_file)

                # Deduplicate incidents by (file_path, line_number)
                seen_line_keys = set()
                deduped_raw = []
                for raw in raw_incidents:
                    dedup_key = (raw.file_path, raw.line_number, raw.variable_name)
                    if dedup_key not in seen_line_keys:
                        seen_line_keys.add(dedup_key)
                        deduped_raw.append(raw)

                # Build and Save Incidents
                for raw in deduped_raw:
                    inc_model = self.incident_builder.build_incident(job_id, raw)
                    self.repo.save_incident(inc_model)
                    incidents_list.append(inc_model)
                    self._update_job_counters(job, inc_model.criticality)

                # Update cache
                CacheEngine.update_cache(file_path, current_hash, len(deduped_raw))
                self.repo.update_job(job)

        finally:
            discovery.cleanup()

        end_time = time.time()
        job.duration_ms = (end_time - start_time) * 1000
        total_processed = analyzed_count + cached_count
        job.throughput_files_per_sec = (total_processed / (job.duration_ms / 1000)) if job.duration_ms > 0 else 0

        # AI Enrichment (if critical or requested)
        if run_ai or job.critical_count > 0:
            job.ai_summary = await self.ollama_client.generate_summary(incidents_list)

        job.status = "COMPLETED"
        job.completed_at = datetime.now().isoformat()
        self.repo.update_job(job)
        await bus.publish(Event("JobCompleted", {"job_id": job_id, "incidents": len(incidents_list)}))

    def _update_job_counters(self, job: JobModel, criticality: str):
        if criticality == "CRÍTICO":
            job.critical_count += 1
        elif criticality == "ALTO":
            job.high_count += 1
        elif criticality == "MÉDIO":
            job.medium_count += 1
        else:
            job.low_count += 1
