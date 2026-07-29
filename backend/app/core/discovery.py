import os
import yaml
from pathlib import Path
from typing import List

CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config.yaml"

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

class DiscoveryEngine:
    DEFAULT_IGNORE_DIRS = {
        "node_modules", ".git", "dist", "build", ".venv", "venv", "vendor", "coverage",
        "docs", "documentation", "site", "__tests__", "tests", "test", "spec", "specs",
        "fixtures", "mocks", "mock", "examples", "example", "target", "bin", "obj",
        "third_party", "deps", "tmp", "temp", ".next", ".nuxt", "out", ".github", ".idea", ".vscode"
    }

    MAX_FILES_PER_REPO = 1000  # Cap máximo de arquivos por repositório para evitar repos gigantes de 34k arquivos

    def __init__(self, target_path: str):
        self.target_path = Path(target_path).resolve()
        self.config = load_config()
        configured_ignores = set(self.config.get("scanner", {}).get("ignore_directories", []))
        self.ignore_dirs = self.DEFAULT_IGNORE_DIRS.union(configured_ignores)

    def discover_files(self) -> List[Path]:
        discovered = []
        if not self.target_path.exists():
            return []

        if self.target_path.is_file():
            return [self.target_path]

        for root, dirs, files in os.walk(self.target_path):
            # Exclude ignored directories in-place
            dirs[:] = [d for d in dirs if d.lower() not in self.ignore_dirs and not d.startswith(".")]

            for file in files:
                file_path = Path(root) / file
                if self._should_inspect(file_path):
                    discovered.append(file_path)
                    if len(discovered) >= self.MAX_FILES_PER_REPO:
                        return discovered

        return discovered

    def _should_inspect(self, path: Path) -> bool:
        name = path.name.lower()
        
        # Ignores minified files, lockfiles, and source maps
        if any(ignored in name for ignored in [".min.js", ".min.css", ".map", "-lock.json", "lock.yaml", "yarn.lock", "cargo.lock", "poetry.lock"]):
            return False

        if ".env" in name:
            return True

        valid_extensions = (
            ".yaml", ".yml", ".json", ".tf", ".tfvars", ".pem", ".key",
            ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".php",
            ".rb", ".c", ".cpp", ".h", ".cs", ".sh", ".ps1", ".ini",
            ".conf", ".properties", ".xml"
        )
        return name.endswith(valid_extensions)
