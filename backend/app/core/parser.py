from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ParsedLine:
    line_number: int
    raw_content: str
    key: Optional[str] = None
    value: Optional[str] = None

@dataclass
class ParsedFile:
    file_path: Path
    relative_path: str
    lines: List[ParsedLine]

class ParserEngine:
    @staticmethod
    def parse_file(file_path: Path, root_path: Path) -> ParsedFile:
        try:
            relative_path = str(file_path.relative_to(root_path))
        except ValueError:
            relative_path = file_path.name

        parsed_lines = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, start=1):
                    line_str = line.strip()
                    if not line_str or line_str.startswith("#") or line_str.startswith("//"):
                        continue
                    
                    key, val = ParserEngine._extract_key_value(line_str)
                    parsed_lines.append(
                        ParsedLine(
                            line_number=line_num,
                            raw_content=line_str,
                            key=key,
                            value=val
                        )
                    )
        except Exception:
            pass

        return ParsedFile(
            file_path=file_path,
            relative_path=relative_path,
            lines=parsed_lines
        )

    @staticmethod
    def _extract_key_value(line: str) -> (Optional[str], Optional[str]):
        if "=" in line:
            parts = line.split("=", 1)
            key = parts[0].replace("export ", "").strip()
            val = parts[1].strip().strip("'\"")
            return key, val
        elif ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip().strip("'\"")
            return key, val
        return None, line
