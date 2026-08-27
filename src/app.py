import os
import json
import csv
import io
import time
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .database import get_db, init_db

app = FastAPI(
    title="HR Business OS / ERP — Hemanth Ranam Professional Services",
    description="All-in-One Small-Business Operating System & Enterprise Resource Planning Control Plane.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BRANDING_FILE = os.path.join(os.path.dirname(__file__), "branding.json")

def load_branding():
    if os.path.exists(BRANDING_FILE):
        with open(BRANDING_FILE, "r") as f:
            return json.load(f)
    return {
        "brand_name": "Hemanth Ranam Professional Services",
        "product_name": "HR Business OS / ERP",
        "theme": {"primary_color": "#2563eb", "bg_canvas": "#ffffff"}
    }

@app.on_event("startup")
def on_startup():
    init_db()

# --- Pydantic Schemas ---
class TenantCreate(BaseModel):
    company_name: str
    admin_email: str
    plan_tier: Optional[str] = "Standard"
    domain: Optional[str] = None
    modules: Optional[List[str]] = ["crm", "accounts", "hrms", "stock", "helpdesk"]

class ProvisionSiteRequest(BaseModel):
    tenant_code: str
    site_domain: str
    admin_password: str

# --- API Endpoints ---

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "HR Business OS / ERP",
        "version": "1.0.0",
        "database": "SQLite WAL Control Plane"
    }

@app.get("/api/branding")
def branding():
    return load_branding()

@app.get("/api/stats")
def get_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        total_tenants = cursor.execute("SELECT COUNT(*) FROM tenants").fetchone()[0]
        active_tenants = cursor.execute("SELECT COUNT(*) FROM tenants WHERE status = 'Active'").fetchone()[0]
        total_modules = cursor.execute("SELECT COUNT(*) FROM modules WHERE is_installed = 1").fetchone()[0]
        
        consolidation = cursor.execute("SELECT total_revenue, total_expenses, net_profit FROM consolidation_metrics ORDER BY id DESC LIMIT 1").fetchone()
        revenue = consolidation[0] if consolidation else 125000.0
        expenses = consolidation[1] if consolidation else 48000.0
        net_profit = consolidation[2] if consolidation else 77000.0

    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_modules": total_modules,
        "consolidated_revenue": revenue,
        "consolidated_expenses": expenses,
        "consolidated_profit": net_profit
    }

# Modules Catalog
@app.get("/api/modules")
def list_modules():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM modules ORDER BY category, name").fetchall()
        return [dict(r) for r in rows]

# Tenants CRUD
@app.get("/api/tenants")
def list_tenants(status: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM tenants WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["modules_enabled"] = json.loads(d["modules_enabled"])
            except:
                pass
            result.append(d)
        return result

@app.post("/api/tenants", status_code=201)
def create_tenant(req: TenantCreate):
    tenant_code = f"TNT-{uuid.uuid4().hex[:6].upper()}"
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO tenants (tenant_code, company_name, admin_email, plan_tier, domain, status, modules_enabled)
            VALUES (?, ?, ?, ?, ?, 'Active', ?)
            """, (tenant_code, req.company_name, req.admin_email, req.plan_tier, req.domain, json.dumps(req.modules)))
            conn.commit()
            return {"id": cursor.lastrowid, "tenant_code": tenant_code, **req.model_dump(), "status": "Active"}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Tenant with this email or domain already exists")

@app.post("/api/provision-site")
def provision_site(req: ProvisionSiteRequest):
    # Simulated Frappe / Docker Bench Site Creation
    time.sleep(0.1)
    return {
        "status": "provisioned",
        "tenant_code": req.tenant_code,
        "site_domain": req.site_domain,
        "admin_url": f"https://{req.site_domain}/login",
        "message": "Enterprise ERP site provisioned successfully with Hemanth Ranam brand layer."
    }

# Data Export
@app.get("/api/export/csv")
def export_csv():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, tenant_code, company_name, admin_email, plan_tier, domain, status, created_at
            FROM tenants
            ORDER BY created_at DESC
        """).fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Tenant Code", "Company Name", "Admin Email", "Plan Tier", "Domain", "Status", "Created At"])
    for r in rows:
        writer.writerow(list(r))
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=hr_business_os_tenants.csv"})

@app.get("/api/export/json")
def export_json():
    with get_db() as conn:
        tenants = [dict(r) for r in conn.execute("SELECT * FROM tenants").fetchall()]
        modules = [dict(r) for r in conn.execute("SELECT * FROM modules").fetchall()]
        metrics = [dict(r) for r in conn.execute("SELECT * FROM consolidation_metrics").fetchall()]
    return JSONResponse(content={
        "metadata": {"exporter": "Hemanth Ranam Professional Services - HR Business OS / ERP", "version": "1.0.0"},
        "tenants": tenants,
        "modules": modules,
        "consolidation_metrics": metrics
    })

# HTML Dashboard Interface
UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HR Business OS / ERP — Hemanth Ranam</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #2563eb;
      --deep-blue: #1d4ed8;
      --canvas: #ffffff;
      --secondary-bg: #f8fafc;
      --card-border: #e2e8f0;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --radius: 12px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', sans-serif; background: var(--secondary-bg); color: var(--text-main); line-height: 1.5; }
    .header { background: white; border-bottom: 1px solid var(--card-border); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
    .logo-badge { font-weight: 700; font-size: 1.25rem; color: var(--primary); display: flex; align-items: center; gap: 0.5rem; }
    .logo-badge span { background: var(--primary); color: white; padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.875rem; }
    .container { max-width: 1280px; margin: 2rem auto; padding: 0 1.5rem; }
    .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }
    .metric-card { background: white; padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--card-border); }
    .metric-val { font-size: 1.75rem; font-weight: 700; margin-top: 0.25rem; }
    .tabs { display: flex; gap: 1rem; border-bottom: 1px solid var(--card-border); margin-bottom: 1.5rem; }
    .tab { padding: 0.75rem 1rem; cursor: pointer; font-weight: 600; color: var(--text-muted); border-bottom: 2px solid transparent; }
    .tab.active { color: var(--primary); border-bottom-color: var(--primary); }
    .card { background: white; border-radius: var(--radius); border: 1px solid var(--card-border); overflow: hidden; margin-bottom: 1.5rem; }
    table { width: 100%; border-collapse: collapse; text-align: left; }
    th { background: var(--secondary-bg); padding: 0.875rem 1.25rem; font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); border-bottom: 1px solid var(--card-border); }
    td { padding: 1rem 1.25rem; border-bottom: 1px solid var(--card-border); font-size: 0.875rem; }
    .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; background: #eff6ff; color: var(--primary); }
    .badge-active { background: #ecfdf5; color: #059669; }
    .btn { background: var(--primary); color: white; border: none; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.875rem; }
    .btn-secondary { background: white; color: var(--text-main); border: 1px solid var(--card-border); }
  </style>
</head>
<body>
  <header class="header">
    <div class="logo-badge"><span>HR</span> HR Business OS / ERP Control Plane</div>
    <div style="display: flex; gap: 0.5rem;">
      <button class="btn btn-secondary" onclick="window.location.href='/api/export/csv'">Export CSV</button>
      <button class="btn btn-secondary" onclick="window.location.href='/api/export/json'">Full Backup</button>
      <button class="btn" onclick="openNewTenantModal()">+ Provision Tenant</button>
    </div>
  </header>

  <div class="container">
    <div class="metrics-grid">
      <div class="metric-card"><small style="color:var(--text-muted);">Active ERP Client Sites</small><div class="metric-val" id="m-tnt">--</div></div>
      <div class="metric-card"><small style="color:var(--text-muted);">Installed Enterprise Modules</small><div class="metric-val" id="m-mod">--</div></div>
      <div class="metric-card"><small style="color:var(--text-muted);">Consolidated Revenue</small><div class="metric-val" id="m-rev" style="color:#059669;">--</div></div>
      <div class="metric-card"><small style="color:var(--text-muted);">Consolidated Net Profit</small><div class="metric-val" id="m-prof" style="color:var(--primary);">--</div></div>
    </div>

    <div class="tabs">
      <div class="tab active" onclick="switchTab('tenants')">Provisioned Client Tenants</div>
      <div class="tab" onclick="switchTab('modules')">Business OS Module Catalog</div>
    </div>

    <div id="tab-tenants" class="card">
      <table>
        <thead>
          <tr>
            <th>Tenant Code</th>
            <th>Company Name</th>
            <th>Admin Email</th>
            <th>Plan Tier</th>
            <th>Domain</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody id="tenants-tbody">
          <tr><td colspan="6" style="text-align:center;">Loading tenants...</td></tr>
        </tbody>
      </table>
    </div>

    <div id="tab-modules" class="card" style="display: none;">
      <table>
        <thead>
          <tr>
            <th>Module Name</th>
            <th>Category</th>
            <th>Description</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody id="modules-tbody">
          <tr><td colspan="4" style="text-align:center;">Loading modules...</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <script>
    async function loadData() {
      const statsRes = await fetch('/api/stats');
      const stats = await statsRes.json();
      document.getElementById('m-tnt').innerText = stats.active_tenants;
      document.getElementById('m-mod').innerText = stats.total_modules;
      document.getElementById('m-rev').innerText = '$' + Number(stats.consolidated_revenue).toLocaleString();
      document.getElementById('m-prof').innerText = '$' + Number(stats.consolidated_profit).toLocaleString();

      const tRes = await fetch('/api/tenants');
      const tenants = await tRes.json();
      const tBody = document.getElementById('tenants-tbody');
      tBody.innerHTML = tenants.map(t => `
        <tr>
          <td><code>${t.tenant_code}</code></td>
          <td><strong>${t.company_name}</strong></td>
          <td>${t.admin_email}</td>
          <td><span class="badge">${t.plan_tier}</span></td>
          <td><a href="https://${t.domain}" target="_blank">${t.domain || 'subdomain.hr.app'}</a></td>
          <td><span class="badge badge-active">${t.status}</span></td>
        </tr>
      `).join('');

      const mRes = await fetch('/api/modules');
      const modules = await mRes.json();
      const mBody = document.getElementById('modules-tbody');
      mBody.innerHTML = modules.map(m => `
        <tr>
          <td><strong>${m.name}</strong></td>
          <td><span class="badge">${m.category}</span></td>
          <td>${m.description}</td>
          <td><span class="badge badge-active">Installed</span></td>
        </tr>
      `).join('');
    }

    function switchTab(tab) {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById('tab-tenants').style.display = tab === 'tenants' ? 'block' : 'none';
      document.getElementById('tab-modules').style.display = tab === 'modules' ? 'block' : 'none';
    }

    async function openNewTenantModal() {
      const name = prompt("Enter Client Company Name:", "Apex Logistics Ltd");
      if (!name) return;
      const email = prompt("Enter Client Administrator Email:", "admin@apexlogistics.co.uk");
      if (!email) return;
      const domain = prompt("Enter Custom Domain / Subdomain:", "apex.hemanth-ranam.com");
      if (!domain) return;

      const payload = {
        company_name: name,
        admin_email: email,
        plan_tier: "Enterprise",
        domain: domain,
        modules: ["crm", "accounts", "hrms", "stock", "helpdesk"]
      };

      const res = await fetch('/api/tenants', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        alert("🎉 Enterprise ERP Tenant provisioned!");
        loadData();
      }
    }

    window.onload = loadData;
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return UI_HTML
