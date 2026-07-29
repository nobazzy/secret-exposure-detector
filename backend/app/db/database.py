import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "scans.db"

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Jobs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        target_path TEXT NOT NULL,
        status TEXT NOT NULL,
        total_files INTEGER DEFAULT 0,
        analyzed_files INTEGER DEFAULT 0,
        cached_files INTEGER DEFAULT 0,
        critical_count INTEGER DEFAULT 0,
        high_count INTEGER DEFAULT 0,
        medium_count INTEGER DEFAULT 0,
        low_count INTEGER DEFAULT 0,
        duration_ms REAL DEFAULT 0.0,
        throughput_files_per_sec REAL DEFAULT 0.0,
        ai_summary TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME
    );
    """)

    # Incidents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        variable_name TEXT NOT NULL,
        secret_value TEXT,
        line_number INTEGER NOT NULL,
        capability TEXT NOT NULL,
        context_type TEXT NOT NULL,
        risk_score INTEGER NOT NULL,
        criticality TEXT NOT NULL,
        policy_overrides TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
    );
    """)

    # SHA256 Cache Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS file_cache (
        file_path TEXT PRIMARY KEY,
        sha256_hash TEXT NOT NULL,
        last_scanned DATETIME DEFAULT CURRENT_TIMESTAMP,
        incidents_count INTEGER DEFAULT 0
    );
    """)

    # Batch Scans Table (Integration with GitRepository Intelligence Indexer)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS batch_scans (
        id TEXT PRIMARY KEY,
        source_query TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        total_repos INTEGER DEFAULT 0,
        completed INTEGER DEFAULT 0,
        failed INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        finished_at DATETIME
    );
    """)

    # Batch Scan Jobs Table (Links batch to individual scan jobs)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS batch_scan_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id TEXT NOT NULL,
        job_id TEXT NOT NULL,
        repository_url TEXT NOT NULL,
        repository_name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        FOREIGN KEY (batch_id) REFERENCES batch_scans (id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

init_db()
