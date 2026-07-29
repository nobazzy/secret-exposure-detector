import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any
from backend.app.db.database import get_connection

class CacheEngine:
    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ""

    @staticmethod
    def is_cached(file_path: Path, current_hash: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sha256_hash FROM file_cache WHERE file_path = ?", (str(file_path),))
        row = cursor.fetchone()
        conn.close()
        if row and row["sha256_hash"] == current_hash:
            return True
        return False

    @staticmethod
    def get_cached_incidents(file_path: Path) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT file_path, relative_path, variable_name, secret_value, line_number,
                   capability, context_type, risk_score, criticality, policy_overrides
            FROM incidents
            WHERE file_path = ?
            ORDER BY id DESC
            """,
            (str(file_path),),
        )
        rows = cursor.fetchall()
        conn.close()
        
        # Deduplicate by variable_name and line_number
        seen = set()
        deduped = []
        for r in rows:
            data = dict(r)
            key = (data["variable_name"], data["line_number"])
            if key not in seen:
                seen.add(key)
                if isinstance(data.get("policy_overrides"), str):
                    try:
                        data["policy_overrides"] = json.loads(data["policy_overrides"])
                    except Exception:
                        data["policy_overrides"] = []
                deduped.append(data)
        return deduped

    @staticmethod
    def update_cache(file_path: Path, current_hash: str, incidents_count: int = 0):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO file_cache (file_path, sha256_hash, last_scanned, incidents_count)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                sha256_hash = excluded.sha256_hash,
                last_scanned = CURRENT_TIMESTAMP,
                incidents_count = excluded.incidents_count
            """,
            (str(file_path), current_hash, incidents_count),
        )
        conn.commit()
        conn.close()
