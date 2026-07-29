import re
import yaml
from pathlib import Path
from typing import List
from backend.app.plugins.base import BaseDetector, RawIncident
from backend.app.core.parser import ParsedFile

def find_rules_dir() -> Path:
    curr = Path(__file__).resolve()
    for parent in [curr] + list(curr.parents):
        candidate = parent / "rules" / "v1"
        if candidate.exists():
            return candidate
    return Path(".") / "rules" / "v1"

RULES_DIR = find_rules_dir()

def load_detectors_yaml():
    path = RULES_DIR / "detectors.yaml"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("detectors", [])
    return []

class EnvDetector(BaseDetector):
    def __init__(self):
        self.rules = load_detectors_yaml()
        self.compiled_rules = []
        for r in self.rules:
            pattern = re.compile(r["pattern"], re.IGNORECASE)
            self.compiled_rules.append((r, pattern))

    @property
    def id(self) -> str:
        return "env_regex_detector"

    @property
    def capability(self) -> str:
        return "general_secret"

    def detect(self, parsed_file: ParsedFile) -> List[RawIncident]:
        incidents = []

        for line in parsed_file.lines:
            target_text = line.key if line.key else line.raw_content
            if not target_text:
                continue

            # Ignore common false positive programming patterns (SQL queries, throw statements, ORM vars, Pydantic type annotations, function/class signatures)
            upper_raw = line.raw_content.upper()
            raw_str = line.raw_content.strip()

            # Ignore SQL queries and DML statements
            if any(sql_kw in upper_raw for sql_kw in ["SELECT ", "UPDATE ", "INSERT INTO ", "DELETE FROM ", "WHERE ", "SET ", "GROUP BY", "ORDER BY", "ON DUPLICATE KEY", "PRIMARY KEY", "FOREIGN KEY", "THROW NEW ERROR", "CONSOLE.LOG"]):
                continue

            # Ignore Python function and Pydantic class definitions
            if raw_str.startswith(("def ", "async def ", "class ", "@app.", "@router.")):
                continue

            # Ignore boolean flag assignments
            if any(b_val in upper_raw for b_val in ["= TRUE", "= FALSE", "= TRUE;", "= FALSE;", "= TRUE,", "= FALSE,"]):
                continue

            # Ignore ORM variables like db_user, db_users, db_session in source code
            if line.key and line.key.strip() in ["db_user", "db_users", "db_session", "db_client", "db_conn"]:
                continue
            if "db_user" in raw_str and ("await" in raw_str or "self.repo" in raw_str or "def " in raw_str or "return" in raw_str or "if " in raw_str):
                continue

            # Ignore Python/TypeScript type annotations without assignment (e.g., DATABASE_URL: str)
            if ":" in raw_str and "=" not in raw_str and any(t in raw_str for t in [": str", ": int", ": bool", ": Optional", ": Dict"]):
                continue

            for rule, pattern in self.compiled_rules:
                if pattern.search(target_text):
                    val = line.value if line.value else target_text
                    if self._is_dummy_value(val):
                        continue

                    var_name = line.key if line.key else target_text
                    incidents.append(
                        RawIncident(
                            file_path=str(parsed_file.file_path),
                            relative_path=parsed_file.relative_path,
                            variable_name=var_name,
                            secret_value=val,
                            line_number=line.line_number,
                            detector_id=rule["id"],
                            capability=rule["capability"],
                            context_type="DotEnvContext",
                        )
                    )
                    break  # Found match for this line

        return incidents

    def _is_dummy_value(self, val: str) -> bool:
        if not val:
            return True
        v = val.strip().lower()

        # Exclude placeholder / dummy secret strings
        if any(d in v for d in ["example", "sample", "your_", "change_me", "changeme", "secret-token", "dummy", "default", "localhost", "127.0.0.1"]):
            return True

        # Exclude uppercase code constants or variable references
        if re.match(r'^[A-Z0-9_]+$', val.strip()):
            return True

        # Exclude plain words without numbers/symbols (e.g. reject, accept, true, false, 512m)
        if re.match(r'^[a-z_\-0-9]{1,8}$', v) and not any(c.isdigit() for c in v if c in "0123456789"):
            return True

        return False
