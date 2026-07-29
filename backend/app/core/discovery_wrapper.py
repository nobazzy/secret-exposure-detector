import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple
import yaml
from backend.app.core.discovery import DiscoveryEngine

CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config.yaml"

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

class DiscoveryEngineWrapper:
    """
    Wrapper que lida tanto com diretórios locais quanto com URLs de repositórios Git (https://github.com/user/repo.git).
    Se for uma URL Git, faz o clone raso (depth 1) em um diretório temporário para inspeção local.
    """
    def __init__(self, target_path: str):
        self.raw_target = target_path.strip()
        self.is_git_url = self.raw_target.startswith(("http://", "https://", "git@")) or self.raw_target.endswith(".git")
        self.temp_dir = None

    def discover_files(self) -> Tuple[List[Path], Path]:
        if self.is_git_url:
            self.temp_dir = tempfile.mkdtemp(prefix="sec_scan_")
            target = Path(self.temp_dir)
            try:
                import subprocess
                # Executa git clone em thread separada com timeout de 30s para não travar o loop de eventos
                def _do_clone():
                    return subprocess.run(
                        ["git", "clone", "--depth", "1", self.raw_target, str(target)],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=30
                    )
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                    future = loop.run_in_executor(None, _do_clone)
                    # Não aguarda o futuro de forma síncrona travante, roda no thread pool
                    import concurrent.futures
                    concurrent.futures.wait([future], timeout=35)
                except RuntimeError:
                    _do_clone()
            except Exception as e:
                return [], target
        else:
            target = Path(self.raw_target).resolve()

        engine = DiscoveryEngine(str(target))
        files = engine.discover_files()
        return files, target

    def cleanup(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
