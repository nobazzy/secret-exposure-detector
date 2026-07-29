from backend.app.plugins.base import RawIncident
from backend.app.db.models import IncidentModel
from backend.app.core.risk_engine import RiskEngine
from backend.app.core.policies import PolicyEngine

class IncidentBuilder:
    def __init__(self):
        self.risk_engine = RiskEngine()
        self.policy_engine = PolicyEngine()

    def build_incident(self, job_id: str, raw: RawIncident) -> IncidentModel:
        base_score, base_criticality = self.risk_engine.calculate_score(raw.capability, raw.file_path)
        
        final_score, final_criticality, applied_policies = self.policy_engine.apply_policies(
            file_path=raw.file_path,
            secret_value=raw.secret_value or "",
            current_score=base_score,
            current_criticality=base_criticality
        )

        return IncidentModel(
            job_id=job_id,
            file_path=raw.file_path,
            relative_path=raw.relative_path,
            variable_name=raw.variable_name,
            secret_value=raw.secret_value,
            line_number=raw.line_number,
            capability=raw.capability,
            context_type=raw.context_type,
            risk_score=final_score,
            criticality=final_criticality,
            policy_overrides=applied_policies
        )
