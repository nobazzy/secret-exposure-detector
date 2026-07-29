import httpx
import yaml
from pathlib import Path
from typing import List, Optional
from backend.app.db.models import IncidentModel

CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config.yaml"

def load_ollama_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("ollama", {})
    return {}

class OllamaClient:
    def __init__(self):
        self.config = load_ollama_config()
        self.enabled = self.config.get("enabled", True)
        self.base_url = self.config.get("base_url", "http://localhost:11434")
        self.model = self.config.get("model", "llama3")
        self.timeout = self.config.get("timeout_seconds", 60)

    async def generate_summary(self, incidents: List[IncidentModel]) -> Optional[str]:
        if not self.enabled or not incidents:
            return self._fallback_summary(incidents)

        prompt = self._build_prompt(incidents)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False}
                )
                if res.status_code == 200:
                    return res.json().get("response", "")
        except Exception:
            pass

        return self._fallback_summary(incidents)

    def _build_prompt(self, incidents: List[IncidentModel]) -> str:
        summary_items = [f"- {inc.variable_name} em {inc.relative_path} (Nível: {inc.criticality})" for inc in incidents[:10]]
        items_str = "\n".join(summary_items)
        return (
            "Você é um especialista em auditoria de segurança cibernética.\n"
            "Análise os seguintes incidentes de exposição acidental de credenciais detectados em um repositório:\n\n"
            f"{items_str}\n\n"
            "Gere um breve resumo executivo (em português) destacando o risco operacional e 3 passos prioritários de remediação."
        )

    def _fallback_summary(self, incidents: List[IncidentModel]) -> str:
        crit_count = sum(1 for i in incidents if i.criticality == "CRÍTICO")
        return (
            f"**Resumo de Auditoria (Modo Fallback / Local):**\n"
            f"Foram identificados {len(incidents)} incidentes ({crit_count} críticos).\n\n"
            "**Ações Recomendadas:**\n"
            "1. Remova imediatamente arquivos `.env` do controle de versão e inclua-os no `.gitignore`.\n"
            "2. Proceda com a rotação imediata das credenciais expostas nos painéis dos respectivos provedores.\n"
            "3. Utilize variáveis de ambiente no nível de sistema ou um Vault de segredos."
        )
