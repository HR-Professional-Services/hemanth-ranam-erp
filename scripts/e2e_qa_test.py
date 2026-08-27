#!/usr/bin/env python3
"""
HR Business OS — Control Plane, Application Registry & Multi-Tenant Simulation E2E Test
"""

import os
import sys
import tempfile
from pathlib import Path

test_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
test_db.close()
os.environ["ERP_DB_PATH"] = test_db.name

sys.path.insert(0, str(Path(__file__).parent.parent))
from fastapi.testclient import TestClient
from src.app import app
from src.database import init_db

def run_erp_qa():
    print("==================================================")
    print("🧪 REAL-WORLD QA SIMULATION: 08 — HR BUSINESS OS")
    print("==================================================")
    init_db(test_db.name)
    client = TestClient(app)

    # 1. Health & Branding
    health = client.get("/api/health")
    assert health.status_code == 200
    branding = client.get("/api/branding")
    assert branding.status_code == 200
    assert branding.json()["product_name"] == "HR Business OS"
    print("✅ [1/7] Health & Institutional Branding verified.")

    # 2. Central Application Registry Query
    registry = client.get("/api/registry").json()
    assert len(registry) == 8
    print(f"✅ [2/7] Application registry verified: {len(registry)} applications registered (Ports 8001–8009).")

    # 3. Multi-Tenant Provisioning
    t_res = client.post("/api/tenants", json={
        "company_name": "Oakwood Retail Services",
        "admin_email": "admin@oakwoodretail.co.uk",
        "plan_tier": "Growth",
        "monthly_fee_gbp": 350.00,
        "modules_enabled": ["pos", "accounts", "crm"]
    })
    assert t_res.status_code == 201
    tenant = t_res.json()
    print(f"✅ [3/7] Tenant provisioned: {tenant['tenant_code']} (Status: {tenant['status']}).")

    # 4. Database Snapshot Verification
    bkp_res = client.post("/api/backups", json={"database_name": "crm.db"})
    assert bkp_res.status_code == 201
    bkp = bkp_res.json()
    print(f"✅ [4/7] Database snapshot created: {bkp['backup_id']} (Status: {bkp['status']}).")

    # 5. Dashboard Platform Metrics
    stats = client.get("/api/dashboard/stats").json()
    assert stats["active_tenants"] >= 4
    assert stats["monthly_recurring_revenue"] >= 1420.0
    print(f"✅ [5/7] Control plane metrics calculated (Active Tenants: {stats['active_tenants']}, MRR: £{stats['monthly_recurring_revenue']:,.2f}).")

    # 6. Tenant List Query
    tenants = client.get("/api/tenants").json()
    assert len(tenants) >= 5
    print("✅ [6/7] Multi-tenant subscription roster queried.")

    # 7. CSV & JSON Export
    assert client.get("/api/export/csv").status_code == 200
    assert client.get("/api/export/json").status_code == 200
    print("✅ [7/7] CSV and JSON data sovereignty exports verified.")

    print("\n🎉 ALL REAL-WORLD HR BUSINESS OS QA TESTS PASSED WITH 100% SUCCESS!\n")

    if os.path.exists(test_db.name):
        os.remove(test_db.name)

if __name__ == "__main__":
    run_erp_qa()
