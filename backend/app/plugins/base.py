from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from backend.app.core.parser import ParsedFile, ParsedLine

@dataclass
class RawIncident:
    file_path: str
    relative_path: str
    variable_name: str
    secret_value: Optional[str]
    line_number: int
    detector_id: str
    capability: str
    context_type: str

class BaseDetector(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def capability(self) -> str:
        pass

    @abstractmethod
    def detect(self, parsed_file: ParsedFile) -> List[RawIncident]:
        pass


class BaseContext(ABC):
    @property
    @abstractmethod
    def context_type(self) -> str:
        pass

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        pass
