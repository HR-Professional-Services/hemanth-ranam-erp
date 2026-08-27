#!/usr/bin/env python3
"""
HR Business OS / ERP — Comprehensive Real-World Multi-Tenant & Provisioning QA Test
Simulates tenant creation, module activation, site provisioning, and consolidation metrics.
"""

import os
import sys
import tempfile
from pathlib import Path

# Set up isolated test DB
test_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
os.environ["ERP_DB_PATH"] = test_db.name

sys.path.insert(0, str(Path(__file__).parent.parent))
from fastapi.testclient import TestClient
from src.app import app
from src.database import init_db

def run_erp_qa():
    print("==================================================")
    print("🧪 STARTING REAL-WORLD QA AUDIT: 08 — HR BUSINESS OS / ERP")
    print("==================================================")
    init_db(test_db.name)
    client = TestClient(app)

    # 1. Health & Branding
    health = client.get("/api/health")
    assert health.status_code == 200
    branding = client.get("/api/branding")
    assert branding.status_code == 200
    assert branding.json()["product_name"] == "HR Business OS / ERP"
    print("✅ [1/7] Health & Branding verified.")

    # 2. ERP Enterprise Modules Catalog
    mods_res = client.get("/api/modules")
    assert mods_res.status_code == 200
    mods = mods_res.json()
    assert len(mods) >= 5
    mod_codes = [m["code"] for m in mods]
    assert "crm" in mod_codes
    assert "accounts" in mod_codes
    assert "hrms" in mod_codes
    print(f"✅ [2/7] ERP enterprise modules catalog verified ({len(mods)} active modules installed).")

    # 3. Multi-Tenant Enterprise Workspace Creation
    tenant_res = client.post("/api/tenants", json={
        "company_name": "Apex Precision Engineering Ltd",
        "admin_email": "operations@apexengineering.co.uk",
        "plan_tier": "Enterprise Custom",
        "domain": "apex.hr-services.com",
        "modules": ["crm", "accounts", "hrms", "stock", "helpdesk"]
    })
    assert tenant_res.status_code == 201
    tenant = tenant_res.json()
    t_code = tenant["tenant_code"]
    assert tenant["status"] == "Active"
    print(f"✅ [3/7] Tenant provisioned: {tenant['company_name']} (Code: {t_code}, Plan: {tenant['plan_tier']}).")

    # 4. Automated ERP Site Provisioning
    prov_res = client.post("/api/provision-site", json={
        "tenant_code": t_code,
        "site_domain": "apex.hr-services.com",
        "admin_password": "SecureEnterprisePassword2026!"
    })
    assert prov_res.status_code == 200
    prov_data = prov_res.json()
    assert prov_data["status"] == "provisioned"
    assert "apex.hr-services.com" in prov_data["admin_url"]
    print("✅ [4/7] Dedicated white-labelled ERP tenant site provisioned successfully.")

    # 5. Multi-Tenant Directory Listing
    tenants = client.get("/api/tenants").json()
    assert any(t["tenant_code"] == t_code for t in tenants)
    print("✅ [5/7] Tenant directory indexing verified.")

    # 6. Global ERP Consolidation Metrics
    stats = client.get("/api/stats").json()
    assert stats["total_tenants"] >= 1
    assert stats["consolidated_revenue"] > 0
    assert stats["consolidated_profit"] > 0
    print(f"✅ [6/7] Consolidated enterprise financials verified (Revenue: £{stats['consolidated_revenue']:,.2f}, Profit: £{stats['consolidated_profit']:,.2f}).")

    # 7. Complete Data Sovereignty Export
    csv_res = client.get("/api/export/csv")
    assert csv_res.status_code == 200
    assert "Apex Precision Engineering" in csv_res.text
    json_res = client.get("/api/export/json")
    assert json_res.status_code == 200
    assert len(json_res.json()["tenants"]) >= 1
    print("✅ [7/7] Complete CSV and JSON ERP control plane database exports verified.")

    print("\n🎉 ALL REAL-WORLD HR BUSINESS OS / ERP QA TESTS PASSED WITH ZERO DEFECTS!\n")

    # Cleanup
    if os.path.exists(test_db.name):
        os.remove(test_db.name)

if __name__ == "__main__":
    run_erp_qa()
