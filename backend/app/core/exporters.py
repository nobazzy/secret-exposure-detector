import json
import csv
from io import StringIO
from typing import List
from backend.app.db.models import JobModel, IncidentModel

class Exporters:
    @staticmethod
    def to_json(job: JobModel, incidents: List[IncidentModel]) -> str:
        data = {
            "job": job.model_dump(),
            "incidents": [inc.model_dump() for inc in incidents]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    @staticmethod
    def to_csv(incidents: List[IncidentModel]) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Job ID", "Arquivo", "Variável", "Linha", "Capacidade",
            "Contexto", "Score Risco", "Criticidade"
        ])
        for inc in incidents:
            writer.writerow([
                inc.id, inc.job_id, inc.relative_path, inc.variable_name,
                inc.line_number, inc.capability, inc.context_type,
                inc.risk_score, inc.criticality
            ])
        return output.getvalue()

    @staticmethod
    def to_sarif(job: JobModel, incidents: List[IncidentModel]) -> str:
        results = []
        for inc in incidents:
            results.append({
                "ruleId": f"SEC-{inc.capability.upper()}",
                "level": "error" if inc.criticality == "CRÍTICO" else "warning",
                "message": {
                    "text": f"Exposição de credencial sensível detectada: {inc.variable_name} (Capacidade: {inc.capability})"
                },
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": inc.relative_path
                        },
                        "region": {
                            "startLine": inc.line_number
                        }
                    }
                }]
            })

        sarif_data = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "Critical Secret Exposure Detector",
                        "version": "4.1.0",
                        "informationUri": "https://github.com/security/secret-detector"
                    }
                },
                "results": results
            }]
        }
        return json.dumps(sarif_data, indent=2)

    @staticmethod
    def to_markdown(job: JobModel, incidents: List[IncidentModel]) -> str:
        lines = [
            f"# Relatório de Auditoria de Segredos - Job {job.id}",
            f"**Data:** {job.created_at or 'Recente'}",
            f"**Caminho Alvo:** `{job.target_path}`",
            f"**Total Analisado:** {job.analyzed_files} arquivos ({job.cached_files} via cache)",
            f"**Tempo Decorrido:** {job.duration_ms:.2f} ms",
            "",
            "## Resumo de Criticidade",
            f"- 🔴 **CRÍTICO:** {job.critical_count}",
            f"- 🟠 **ALTO:** {job.high_count}",
            f"- 🟡 **MÉDIO:** {job.medium_count}",
            f"- 🟢 **BAIXO:** {job.low_count}",
            "",
            "## Incidentes Detectados",
            "| Arquivo | Variável | Linha | Capacidade | Score | Criticidade |",
            "| :--- | :--- | :---: | :--- | :---: | :---: |"
        ]
        for inc in incidents:
            lines.append(
                f"| `{inc.relative_path}` | `{inc.variable_name}` | {inc.line_number} | {inc.capability} | {inc.risk_score} | {inc.criticality} |"
            )
        return "\n".join(lines)
