from backend.app.plugins.base import BaseContext

class DotEnvContext(BaseContext):
    @property
    def context_type(self) -> str:
        return "DotEnvContext"

    def supports(self, file_path: str) -> bool:
        lower = file_path.lower()
        return ".env" in lower or lower.endswith((".config", ".yaml", ".yml", ".json"))
