import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from src.app import app
from src.database import init_db

@pytest.fixture
def client():
    test_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    test_db.close()
    os.environ["ERP_DB_PATH"] = test_db.name
    init_db(test_db.name)
    with TestClient(app) as c:
        yield c
    if os.path.exists(test_db.name):
        try:
            os.remove(test_db.name)
        except Exception:
            pass

def test_health_and_branding(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["service"] == "HR Business OS"

    b_res = client.get("/api/branding")
    assert b_res.status_code == 200
    assert b_res.json()["product_name"] == "HR Business OS"

def test_registry_and_tenant_provisioning(client):
    # 1. App Registry
    registry = client.get("/api/registry").json()
    assert len(registry) == 8
    assert any(a["name"] == "HR CRM" for a in registry)

    # 2. Provision Tenant
    t_res = client.post("/api/tenants", json={
        "company_name": "Apex Engineering Ltd",
        "admin_email": "admin@apexengineering.co.uk",
        "plan_tier": "Enterprise",
        "monthly_fee_gbp": 500.0,
        "modules_enabled": ["crm", "accounts", "hrms"]
    })
    assert t_res.status_code == 201
    assert t_res.json()["status"] == "Active"

    # 3. Create Backup Snapshot
    bkp_res = client.post("/api/backups", json={"database_name": "accounts.db"})
    assert bkp_res.status_code == 201
    assert bkp_res.json()["status"] == "Verified"
