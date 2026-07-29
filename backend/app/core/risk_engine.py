import yaml
from pathlib import Path
from typing import Dict, Any

def find_rules_dir() -> Path:
    curr = Path(__file__).resolve()
    for parent in [curr] + list(curr.parents):
        candidate = parent / "rules" / "v1"
        if candidate.exists():
            return candidate
    return Path(".") / "rules" / "v1"

RULES_DIR = find_rules_dir()

def load_capabilities_yaml() -> Dict[str, Any]:
    path = RULES_DIR / "capabilities.yaml"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("capabilities", {})
    return {}

class RiskEngine:
    def __init__(self):
        self.capabilities = load_capabilities_yaml()

    def calculate_score(self, capability_key: str, file_path: str) -> (int, str):
        cap_info = self.capabilities.get(capability_key, {})
        base_score = cap_info.get("weight", 30)

        # Contextual boosts
        lower_path = file_path.lower()
        if "production" in lower_path or "prod" in lower_path:
            base_score += 15
        elif "root" in lower_path or lower_path.count("/") <= 2:
            base_score += 5

        # Classify criticality based on score
        criticality = self._score_to_criticality(base_score)
        return base_score, criticality

    def _score_to_criticality(self, score: int) -> str:
        if score >= 75:
            return "CRÍTICO"
        elif score >= 45:
            return "ALTO"
        elif score >= 20:
            return "MÉDIO"
        else:
            return "BAIXO"
