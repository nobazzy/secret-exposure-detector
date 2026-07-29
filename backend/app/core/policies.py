import re
import yaml
from pathlib import Path
from typing import List, Tuple

def find_rules_dir() -> Path:
    curr = Path(__file__).resolve()
    for parent in [curr] + list(curr.parents):
        candidate = parent / "rules" / "v1"
        if candidate.exists():
            return candidate
    return Path(".") / "rules" / "v1"

RULES_DIR = find_rules_dir()

def load_policies_yaml() -> List[dict]:
    path = RULES_DIR / "policies.yaml"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("policies", [])
    return []

class PolicyEngine:
    def __init__(self):
        self.policies = load_policies_yaml()

    def apply_policies(self, file_path: str, secret_value: str, current_score: int, current_criticality: str) -> Tuple[int, str, List[str]]:
        applied = []
        score = current_score
        criticality = current_criticality

        for pol in self.policies:
            cond = pol.get("condition")
            pattern = pol.get("pattern", "")

            if cond == "filename_matches" and re.search(pattern, file_path, re.IGNORECASE):
                score += pol.get("score_modifier", 0)
                if pol.get("override_criticality"):
                    criticality = pol.get("override_criticality")
                applied.append(pol["id"])

            elif cond == "path_contains" and re.search(pattern, file_path, re.IGNORECASE):
                score += pol.get("score_modifier", 0)
                applied.append(pol["id"])

            elif cond == "value_matches" and secret_value and re.search(pattern, secret_value, re.IGNORECASE):
                score += pol.get("score_modifier", 0)
                if pol.get("override_criticality"):
                    criticality = pol.get("override_criticality")
                applied.append(pol["id"])

        # Cap score between 0 and 100
        score = max(0, min(100, score))
        return score, criticality, applied
