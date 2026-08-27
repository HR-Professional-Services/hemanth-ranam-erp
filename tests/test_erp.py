import pytest
import os
import tempfile
from fastapi.testclient import TestClient

test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
test_db_path = test_db_file.name
os.environ["ERP_DB_PATH"] = test_db_path

from src.app import app
from src.database import init_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db(test_db_path)
    yield
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

@pytest.fixture
def client():
    return TestClient(app)

def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["service"] == "HR Business OS / ERP"

def test_tenant_provisioning(client):
    res = client.post("/api/tenants", json={
        "company_name": "Horizon Quant Capital",
        "admin_email": "ops@horizonquant.com",
        "plan_tier": "Enterprise",
        "domain": "horizon.hemanth-ranam.com",
        "modules": ["crm", "accounts", "hrms", "helpdesk"]
    })
    assert res.status_code == 201
    data = res.json()
    assert data["tenant_code"].startswith("TNT-")
    assert data["status"] == "Active"

def test_tenant_listing(client):
    res = client.get("/api/tenants")
    assert res.status_code == 200
    tenants = res.json()
    assert len(tenants) >= 1
    assert tenants[0]["company_name"] == "Horizon Quant Capital"

def test_site_provisioning_orchestration(client):
    res = client.post("/api/provision-site", json={
        "tenant_code": "TNT-TEST01",
        "site_domain": "tenant.hr.app",
        "admin_password": "SecurePassword123!"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "provisioned"

def test_financial_stats(client):
    res = client.get("/api/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_tenants"] >= 1
