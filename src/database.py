import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.getenv("ERP_DB_PATH", "erp_os.db")

def init_db(db_path: str = DB_PATH):
    """Initializes SQLite database with WAL mode for HR Business OS Management."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor = conn.cursor()

    # Client Tenants Registry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_code TEXT UNIQUE NOT NULL,
        company_name TEXT NOT NULL,
        admin_email TEXT UNIQUE NOT NULL,
        plan_tier TEXT DEFAULT 'Standard', -- Starter, Standard, Enterprise
        domain TEXT UNIQUE,
        status TEXT DEFAULT 'Active', -- Provisioning, Active, Suspended
        modules_enabled TEXT NOT NULL, -- JSON list: ["crm", "accounts", "hrms", "stock", "helpdesk"]
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Enterprise Modules Catalog
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS modules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_key TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        is_installed BOOLEAN DEFAULT 1
    );
    """)

    # Multi-Entity Financial Consolidation Summary
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consolidation_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period TEXT NOT NULL, -- e.g. 2026-Q3
        total_revenue REAL DEFAULT 0.0,
        total_expenses REAL DEFAULT 0.0,
        net_profit REAL DEFAULT 0.0,
        headcount INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

@contextmanager
def get_db(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
    finally:
        conn.close()
