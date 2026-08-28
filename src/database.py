import sqlite3
import os
import hashlib
from typing import Optional
from contextlib import contextmanager

def hash_password(password: str) -> str:
    salt = "hr_business_os_salt_2026"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def get_db_path():
    return os.getenv("ERP_DB_PATH", "erp_os.db")

def init_db(db_path: Optional[str] = None):
    """Initializes SQLite database with WAL mode for HR Business OS Control Plane."""
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path, timeout=20.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor = conn.cursor()

    # 1. Users / Control Plane Admins
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT DEFAULT 'Admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Application Registry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_key TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        port INTEGER NOT NULL,
        url TEXT NOT NULL,
        health_endpoint TEXT NOT NULL,
        version TEXT DEFAULT '2.0.0',
        category TEXT NOT NULL,
        status TEXT DEFAULT 'Online'
    );
    """)

    # 3. Client Tenants Registry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_code TEXT UNIQUE NOT NULL,
        company_name TEXT NOT NULL,
        admin_email TEXT UNIQUE NOT NULL,
        plan_tier TEXT DEFAULT 'Standard', -- 'Starter', 'Growth', 'Enterprise'
        domain TEXT UNIQUE,
        status TEXT DEFAULT 'Active', -- 'Active', 'Provisioning', 'Suspended'
        monthly_fee_gbp REAL DEFAULT 250.0,
        modules_enabled TEXT NOT NULL, -- JSON list
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. System Backups
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        backup_id TEXT UNIQUE NOT NULL,
        database_name TEXT NOT NULL,
        file_size_kb INTEGER NOT NULL,
        status TEXT DEFAULT 'Verified',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Financial Consolidation Metrics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consolidation_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period TEXT NOT NULL,
        total_revenue REAL DEFAULT 0.0,
        total_expenses REAL DEFAULT 0.0,
        net_profit REAL DEFAULT 0.0,
        headcount INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed Admin User if empty
    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO users (email, password_hash, full_name, role)
        VALUES (?, ?, ?, ?);
        """, ("admin@demo.local", hash_password("demo123"), "Control Plane Lead", "Admin"))

    # Seed Application Registry
    cursor.execute("DELETE FROM app_registry WHERE app_key IN ('pos', 'automation');")
    cursor.execute("SELECT COUNT(*) FROM app_registry;")
    if cursor.fetchone()[0] == 0:
        apps = [
            ("crm", "HR CRM", 8001, "http://localhost:8001", "http://127.0.0.1:8001/api/health", "2.0.0", "Growth", "Online"),
            ("booking", "HR Bookings", 8002, "http://localhost:8002", "http://127.0.0.1:8002/api/health", "2.0.0", "Operations", "Online"),
            ("accounts", "HR Accounts", 8004, "http://localhost:8004", "http://127.0.0.1:8004/api/health", "2.0.0", "Finance", "Online"),
            ("hrms", "HR People", 8005, "http://localhost:8005", "http://127.0.0.1:8005/api/health", "2.0.0", "Human Resources", "Online"),
            ("helpdesk", "HR Helpdesk", 8006, "http://localhost:8006", "http://127.0.0.1:8006/api/health", "2.0.0", "Support", "Online"),
            ("erp", "HR Business OS", 8008, "http://localhost:8008", "http://127.0.0.1:8008/api/health", "2.0.0", "Central Control Plane", "Online"),
            ("client-portal", "HR Client Portal", 8009, "http://localhost:8009", "http://127.0.0.1:8009/api/health", "2.0.0", "Customer Experience", "Online")
        ]
        cursor.executemany("""
        INSERT OR REPLACE INTO app_registry (app_key, name, port, url, health_endpoint, version, category, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, apps)

    # Seed Default Tenants
    cursor.execute("SELECT COUNT(*) FROM tenants;")
    if cursor.fetchone()[0] == 0:
        tenants = [
            ("TEN-101", "Greenfield Dental Care", "admin@greenfielddental.co.uk", "Enterprise", "dental.hr-suite.local", "Active", 450.0, '["crm", "booking", "accounts", "helpdesk"]'),
            ("TEN-102", "Riverside Fitness & Gym", "admin@riversidefitness.wales", "Growth", "gym.hr-suite.local", "Active", 250.0, '["pos", "booking", "accounts", "hrms"]'),
            ("TEN-103", "Northstar Consulting", "admin@northstar-consulting.com", "Enterprise", "northstar.hr-suite.local", "Active", 600.0, '["crm", "accounts", "automation", "client-portal", "helpdesk"]'),
            ("TEN-104", "Brightline Plumbing Ltd", "admin@brightlineplumbing.co.uk", "Starter", "brightline.hr-suite.local", "Active", 120.0, '["crm", "booking", "accounts"]')
        ]
        cursor.executemany("""
        INSERT INTO tenants (tenant_code, company_name, admin_email, plan_tier, domain, status, monthly_fee_gbp, modules_enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, tenants)

    # Seed Backups
    cursor.execute("SELECT COUNT(*) FROM system_backups;")
    if cursor.fetchone()[0] == 0:
        backups = [
            ("BKP-2026-0801", "crm.db", 380, "Verified"),
            ("BKP-2026-0802", "accounts.db", 420, "Verified"),
            ("BKP-2026-0803", "hrms.db", 310, "Verified"),
            ("BKP-2026-0804", "automations.db", 290, "Verified")
        ]
        cursor.executemany("""
        INSERT INTO system_backups (backup_id, database_name, file_size_kb, status)
        VALUES (?, ?, ?, ?);
        """, backups)

    # Seed Consolidation Metrics
    cursor.execute("SELECT COUNT(*) FROM consolidation_metrics;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO consolidation_metrics (period, total_revenue, total_expenses, net_profit, headcount)
        VALUES ('2026-Q3', 142000.0, 41500.0, 100500.0, 36);
        """)

    conn.commit()
    conn.close()

@contextmanager
def get_db(db_path: Optional[str] = None):
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
    finally:
        conn.close()
