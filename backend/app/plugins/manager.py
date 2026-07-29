from typing import List
from backend.app.plugins.base import BaseDetector, BaseContext, RawIncident
from backend.app.plugins.detectors.env_detector import EnvDetector
from backend.app.plugins.detectors.entropy_detector import EntropyDetector
from backend.app.plugins.contexts.dotenv_context import DotEnvContext
from backend.app.core.parser import ParsedFile

class PluginManager:
    def __init__(self):
        self.detectors: List[BaseDetector] = [
            EnvDetector(),
            EntropyDetector(min_entropy=4.0, min_length=16)
        ]
        self.contexts: List[BaseContext] = [DotEnvContext()]

    def run_detection(self, parsed_file: ParsedFile) -> List[RawIncident]:
        incidents = []
        file_str = str(parsed_file.file_path)

        for detector in self.detectors:
            found = detector.detect(parsed_file)
            incidents.extend(found)

        return incidents
