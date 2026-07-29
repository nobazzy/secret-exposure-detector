import math
import re
from typing import List
from backend.app.plugins.base import BaseDetector, RawIncident
from backend.app.core.parser import ParsedFile

class EntropyDetector(BaseDetector):
    def __init__(self, min_entropy: float = 4.2, min_length: int = 16):
        self.min_entropy = min_entropy
        self.min_length = min_length
        # Token extraction pattern (alphanumeric, dashes, underscores, slashes, plus, equals)
        self.token_pattern = re.compile(r'[A-Za-z0-9_\-\+/=]{16,}')

    @property
    def id(self) -> str:
        return "shannon_entropy_detector"

    @property
    def capability(self) -> str:
        return "private_key"

    def detect(self, parsed_file: ParsedFile) -> List[RawIncident]:
        incidents = []

        for line in parsed_file.lines:
            tokens = self.token_pattern.findall(line.raw_content)

            for token in tokens:
                # Skip common code words / URLs / imports
                if self._is_false_positive(token):
                    continue

                entropy = self._calculate_entropy(token)
                if entropy >= self.min_entropy:
                    var_name = line.key if line.key else f"ENTROPY_HIGH_RANDOMNESS ({entropy:.2f})"
                    incidents.append(
                        RawIncident(
                            file_path=str(parsed_file.file_path),
                            relative_path=parsed_file.relative_path,
                            variable_name=var_name,
                            secret_value=token,
                            line_number=line.line_number,
                            detector_id="high_entropy_token",
                            capability="identity_auth" if "token" in var_name.lower() else "cloud_infrastructure",
                            context_type="SourceCodeEntropyContext",
                        )
                    )
                    break  # One high entropy match per line to avoid duplication

        return incidents

    def _calculate_entropy(self, text: str) -> float:
        if not text:
            return 0.0
        entropy = 0.0
        length = len(text)
        for char in set(text):
            p_x = float(text.count(char)) / length
            entropy -= p_x * math.log2(p_x)
        return entropy

    def _is_false_positive(self, token: str) -> bool:
        # Exclude uppercase code constants (e.g., BACKGROUND_TASK_RESULT_WOKE_SYSTEM_PROMPT, IMAGE_COMPRESS_DEFAULT_QUALITY)
        if re.match(r'^[A-Z0-9_]+$', token):
            return True

        lower = token.lower()
        # Exclude SRI package integrity hashes (e.g. sha512-..., sha256-...)
        if lower.startswith(("sha512-", "sha256-", "sha384-")):
            return True
        # Exclude Clerk public user IDs (e.g. user_2y...) and dummy token names
        if lower.startswith("user_2y") or lower.startswith("dummy"):
            return True
        # Exclude standard URLs, image CDNs, imports, UI component paths, common paths
        if lower.startswith("http") or "unsplash.com" in lower or "node_modules" in lower or lower.startswith("application/"):
            return True
        if any(img_ext in lower for img_ext in [".jpg", ".jpeg", ".png", ".svg", ".gif", ".webp", "photo-"]):
            return True
        if any(ui_path in lower for ui_path in ["/components/", "/pages/", "/views/", "/assets/", "/hooks/", "/services/", "/routes/", "/api/"]):
            return True
        if "nofallthroughcasesinswitch" in lower or "compileroptions" in lower:
            return True
        if lower.count('/') > 3 or lower.count('.') > 2:
            return True
        # Exclude repeated characters or sequential charsets like ABCDEFGHJKLMNPQRSTUVWXYZ...
        if len(set(token)) <= 4 or "abcdefgh" in lower or "123456789" in lower:
            return True
        return False
