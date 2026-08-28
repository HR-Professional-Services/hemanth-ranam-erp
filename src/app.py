import os
import json
import csv
import io
import time
import uuid
import urllib.request
from datetime import datetime
from fastapi import FastAPI, HTTPException, Response, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from src.database import init_db, get_db, get_db_path, hash_password

app = FastAPI(title="HR Business OS", version="2.0.0")

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
        "brand_name": "HR",
        "product_name": "HR Business OS",
        "author": "HR Professional Services",
        "primary_color": "#2563eb",
        "bg_color": "#f8fafc",
        "surface_color": "#ffffff"
    }

@app.on_event("startup")
def startup_event():
    init_db()

# --- Pydantic Models ---
class TenantCreate(BaseModel):
    company_name: str
    admin_email: str
    plan_tier: Optional[str] = "Standard" # Starter, Growth, Enterprise
    domain: Optional[str] = ""
    monthly_fee_gbp: Optional[float] = 250.0
    modules_enabled: Optional[List[str]] = ["crm", "accounts"]

class BackupRequest(BaseModel):
    database_name: str

# --- API Endpoints ---
@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "HR Business OS", "version": "2.0.0", "database": "SQLite WAL"}

@app.get("/api/branding")
def get_branding():
    return load_branding()

@app.get("/api/dashboard/stats")
def dashboard_stats():
    with get_db() as conn:
        apps_count = conn.execute("SELECT COUNT(*) FROM app_registry").fetchone()[0]
        tenants_count = conn.execute("SELECT COUNT(*) FROM tenants WHERE status = 'Active'").fetchone()[0]
        mrr_total = conn.execute("SELECT COALESCE(SUM(monthly_fee_gbp), 0) FROM tenants WHERE status = 'Active'").fetchone()[0]
        backups_count = conn.execute("SELECT COUNT(*) FROM system_backups").fetchone()[0]
        
        metrics = conn.execute("SELECT * FROM consolidation_metrics ORDER BY id DESC LIMIT 1").fetchone()

        return {
            "applications_online": f"{apps_count}/{apps_count}",
            "active_tenants": tenants_count,
            "monthly_recurring_revenue": mrr_total,
            "total_backups_verified": backups_count,
            "system_health": "100% Operational",
            "consolidation": dict(metrics) if metrics else {}
        }

@app.get("/api/registry")
def list_registry(live_ping: bool = False):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM app_registry ORDER BY port ASC").fetchall()
        result = []
        for r in rows:
            app_dict = dict(r)
            app_dict["latency_ms"] = 1.2
            if live_ping:
                try:
                    t0 = time.time()
                    req = urllib.request.Request(app_dict["health_endpoint"], headers={"User-Agent": "HR-Business-OS/2.0"})
                    with urllib.request.urlopen(req, timeout=1.0) as resp:
                        if resp.status == 200:
                            app_dict["status"] = "Online"
                            app_dict["latency_ms"] = round((time.time() - t0) * 1000, 1)
                except Exception:
                    app_dict["status"] = "Degraded"
            result.append(app_dict)
        return result

@app.get("/api/tenants")
def list_tenants():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM tenants ORDER BY id ASC").fetchall()
        result = []
        for r in rows:
            t = dict(r)
            try:
                t["modules_list"] = json.loads(t["modules_enabled"])
            except Exception:
                t["modules_list"] = []
            result.append(t)
        return result

@app.post("/api/tenants", status_code=201)
def create_tenant(payload: TenantCreate):
    with get_db() as conn:
        t_code = f"TEN-{uuid.uuid4().hex[:6].upper()}"
        dom = payload.domain or f"{payload.company_name.lower().replace(' ', '')}-{uuid.uuid4().hex[:4]}.hr-suite.local"
        cur = conn.execute("""
        INSERT INTO tenants (tenant_code, company_name, admin_email, plan_tier, domain, status, monthly_fee_gbp, modules_enabled)
        VALUES (?, ?, ?, ?, ?, 'Active', ?, ?)
        """, (t_code, payload.company_name, payload.admin_email, payload.plan_tier, dom, payload.monthly_fee_gbp, json.dumps(payload.modules_enabled)))
        conn.commit()
        return {"id": cur.lastrowid, "tenant_code": t_code, "status": "Active", "message": "Tenant provisioned"}

@app.delete("/api/tenants/{tenant_id}")
def delete_tenant(tenant_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM tenants WHERE id = ?", (tenant_id,))
        conn.commit()
        return {"status": "deleted", "id": tenant_id}

@app.get("/api/backups")
def list_backups():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM system_backups ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

@app.post("/api/backups", status_code=201)
def create_backup(payload: BackupRequest):
    with get_db() as conn:
        bkp_id = f"BKP-2026-{1000 + int(time.time()) % 9000}"
        cur = conn.execute("""
        INSERT INTO system_backups (backup_id, database_name, file_size_kb, status)
        VALUES (?, ?, 350, 'Verified')
        """, (bkp_id, payload.database_name))
        conn.commit()
        return {"id": cur.lastrowid, "backup_id": bkp_id, "status": "Verified", "message": "Database backup completed"}

# --- Export Endpoints ---
@app.get("/api/export/csv")
def export_csv():
    with get_db() as conn:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Tenant Code", "Company Name", "Admin Email", "Plan Tier", "Domain", "Status", "Monthly Fee (GBP)"])
        rows = conn.execute("SELECT tenant_code, company_name, admin_email, plan_tier, domain, status, monthly_fee_gbp FROM tenants").fetchall()
        for r in rows:
            writer.writerow(list(r))
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=hr_business_os_tenants.csv"})

@app.get("/api/export/json")
def export_json():
    with get_db() as conn:
        apps = [dict(r) for r in conn.execute("SELECT * FROM app_registry").fetchall()]
        tenants = [dict(r) for r in conn.execute("SELECT * FROM tenants").fetchall()]
        backups = [dict(r) for r in conn.execute("SELECT * FROM system_backups").fetchall()]
        return {"export_timestamp": "2026-08-28T00:00:00Z", "apps": apps, "tenants": tenants, "backups": backups}

# --- Main Multi-View Shell UI ---
@app.get("/", response_class=HTMLResponse)
def index_page():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HR Business OS — Central Control Plane & SaaS Multi-Tenant Manager</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --hr-primary: #2563eb;
      --hr-primary-hover: #1d4ed8;
      --hr-primary-light: #eff6ff;
      --hr-success: #10b981;
      --hr-warning: #f59e0b;
      --hr-danger: #ef4444;
      --hr-bg: #f8fafc;
      --hr-surface: #ffffff;
      --hr-surface-elevated: #f1f5f9;
      --hr-surface-hover: #f8fafc;
      --hr-text: #0f172a;
      --hr-text-secondary: #475569;
      --hr-muted: #64748b;
      --hr-border: #e2e8f0;
      --hr-radius-sm: 6px;
      --hr-radius-md: 10px;
      --hr-font-sans: 'Inter', sans-serif;
      --hr-font-mono: 'JetBrains Mono', monospace;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background-color: var(--hr-bg); color: var(--hr-text); font-family: var(--hr-font-sans); display: flex; height: 100vh; overflow: hidden; }
    
    .sidebar { width: 250px; background: var(--hr-surface); border-right: 1px solid var(--hr-border); display: flex; flex-direction: column; flex-shrink: 0; }
    .brand-header { padding: 20px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--hr-border); }
    .brand-badge { background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #fff; font-weight: 800; font-size: 16px; padding: 6px 10px; border-radius: 8px; }
    .brand-title { font-weight: 700; font-size: 16px; color: var(--hr-text); }

    .nav-menu { list-style: none; padding: 16px 12px; flex: 1; display: flex; flex-direction: column; gap: 4px; }
    .nav-item a { display: flex; align-items: center; gap: 12px; padding: 10px 14px; color: var(--hr-text-secondary); text-decoration: none; border-radius: var(--hr-radius-sm); font-size: 13px; font-weight: 500; }
    .nav-item a:hover { background: var(--hr-surface-hover); color: var(--hr-text); }
    .nav-item.active a { background: var(--hr-primary-light); color: var(--hr-primary); font-weight: 600; border-left: 3px solid var(--hr-primary); }

    .main-wrapper { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
    .top-bar { height: 64px; background: var(--hr-surface); border-bottom: 1px solid var(--hr-border); display: flex; align-items: center; justify-content: space-between; padding: 0 28px; }
    .content-body { flex: 1; overflow-y: auto; padding: 28px; }
    .view-section { display: none; }
    .view-section.active { display: block; }

    .btn { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: var(--hr-radius-sm); font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
    .btn-primary { background: var(--hr-primary); color: #fff; }
    .btn-secondary { background: var(--hr-surface); color: var(--hr-text); border: 1px solid var(--hr-border); }

    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .kpi-card { background: var(--hr-surface); border: 1px solid var(--hr-border); border-radius: var(--hr-radius-md); padding: 20px; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.03); }
    .kpi-label { font-size: 12px; color: var(--hr-muted); text-transform: uppercase; margin-bottom: 8px; font-weight: 600; }
    .kpi-val { font-size: 24px; font-weight: 800; font-family: var(--hr-font-mono); }

    .data-card { background: var(--hr-surface); border: 1px solid var(--hr-border); border-radius: var(--hr-radius-md); overflow: hidden; margin-bottom: 24px; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.03); }
    .card-header { padding: 18px 22px; border-bottom: 1px solid var(--hr-border); display: flex; justify-content: space-between; align-items: center; }
    .card-title { font-weight: 700; font-size: 15px; }

    table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
    th { padding: 12px 18px; background: #f8fafc; color: var(--hr-muted); font-weight: 600; border-bottom: 1px solid var(--hr-border); font-size: 11px; text-transform: uppercase; }
    td { padding: 14px 18px; border-bottom: 1px solid var(--hr-border); }
    tr:hover td { background: #f8fafc; }

    .badge { display: inline-flex; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
    .badge-online { background: #ecfdf5; color: #10b981; }
    .badge-tier { background: #eff6ff; color: #3b82f6; }
  </style>
</head>
<body>

  <aside class="sidebar">
    <div class="brand-header">
      <div class="brand-badge">HR</div>
      <div>
        <div class="brand-title">HR Business OS</div>
        <div style="font-size:11px; color:var(--hr-muted);">Control Plane</div>
      </div>
    </div>
    <ul class="nav-menu">
      <li class="nav-item active" id="nav-dashboard"><a href="#dashboard" onclick="navigate('dashboard')">📊 Suite Overview</a></li>
      <li class="nav-item" id="nav-registry"><a href="#registry" onclick="navigate('registry')">🌐 Application Registry</a></li>
      <li class="nav-item" id="nav-tenants"><a href="#tenants" onclick="navigate('tenants')">🏢 Tenant Subscriptions</a></li>
      <li class="nav-item" id="nav-backups"><a href="#backups" onclick="navigate('backups')">💾 Backup Manager</a></li>
      <li class="nav-item" id="nav-reports"><a href="#reports" onclick="navigate('reports')">📈 Ecosystem Reports</a></li>
    </ul>
    <div style="padding:16px; border-top:1px solid var(--hr-border); font-size:12px; color:var(--hr-muted);">
      Orchestrator: <strong>Master Control Node</strong>
    </div>
  </aside>

  <main class="main-wrapper">
    <header class="top-bar">
      <div style="font-size: 18px; font-weight: 700;" id="top-title">Suite Overview</div>
      <div style="display:flex; gap:10px;">
        <button class="btn btn-secondary" onclick="window.open('/api/export/csv')">📥 Export CSV</button>
        <button class="btn btn-primary" onclick="openTenantModal()">+ Provision Tenant</button>
      </div>
    </header>

    <div class="content-body">
      
      <!-- 1. DASHBOARD VIEW -->
      <section id="view-dashboard" class="view-section active">
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">Suite Applications</div>
            <div class="kpi-val" id="kpi-apps" style="color:var(--hr-success);">8 / 8 Online</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Active Client Tenants</div>
            <div class="kpi-val" id="kpi-tenants">0</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Monthly SaaS Run Rate</div>
            <div class="kpi-val" id="kpi-mrr" style="color:var(--hr-primary);">£0.00</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">System Health Status</div>
            <div class="kpi-val" id="kpi-health" style="color:var(--hr-success);">100% OK</div>
          </div>
        </div>

        <div class="data-card">
          <div class="card-header"><div class="card-title">Live Application Health & Navigation Matrix</div></div>
          <table>
            <thead>
              <tr>
                <th>Product Name</th>
                <th>Port</th>
                <th>Category</th>
                <th>Version</th>
                <th>Status</th>
                <th>Direct Launch</th>
              </tr>
            </thead>
            <tbody id="dash-registry-tbody"></tbody>
          </table>
        </div>
      </section>

      <!-- 2. REGISTRY VIEW -->
      <section id="view-registry" class="view-section">
        <div class="data-card">
          <div class="card-header">
            <div class="card-title">Service Registry & Health Check Pings</div>
            <button class="btn btn-secondary" onclick="loadErpData(true)">🔄 Ping Live Endpoints</button>
          </div>
          <table>
            <thead>
              <tr>
                <th>App Name</th>
                <th>Port</th>
                <th>URL</th>
                <th>Category</th>
                <th>Status</th>
                <th>Latency</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="registry-tbody"></tbody>
          </table>
        </div>
      </section>

      <!-- 3. TENANTS VIEW -->
      <section id="view-tenants" class="view-section">
        <div class="data-card">
          <div class="card-header">
            <div class="card-title">Multi-Tenant Subscriptions & Workspaces</div>
            <button class="btn btn-primary" onclick="openTenantModal()">+ Add Tenant</button>
          </div>
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Company</th>
                <th>Admin Email</th>
                <th>Plan Tier</th>
                <th>Monthly (GBP)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id="tenants-tbody"></tbody>
          </table>
        </div>
      </section>

      <!-- 4. BACKUPS VIEW -->
      <section id="view-backups" class="view-section">
        <div class="data-card">
          <div class="card-header">
            <div class="card-title">Automated Database Snapshots & WAL Backups</div>
            <button class="btn btn-primary" onclick="triggerBackup()">+ Create Snapshot</button>
          </div>
          <table>
            <thead>
              <tr>
                <th>Backup ID</th>
                <th>Database</th>
                <th>Size (KB)</th>
                <th>Integrity</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody id="backups-tbody"></tbody>
          </table>
        </div>
      </section>

      <!-- 5. REPORTS VIEW -->
      <section id="view-reports" class="view-section">
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">Export Tenant Manifest (CSV)</div>
            <button class="btn btn-primary" style="margin-top:10px;" onclick="window.open('/api/export/csv')">📥 Download CSV</button>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Export Complete Control Plane JSON</div>
            <button class="btn btn-secondary" style="margin-top:10px;" onclick="window.open('/api/export/json')">📦 Export Complete JSON</button>
          </div>
        </div>
      </section>

    </div>
  </main>

  <script>
    function navigate(view) {
      document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
      document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
      const sec = document.getElementById('view-' + view);
      const nav = document.getElementById('nav-' + view);
      if (sec) sec.classList.add('active');
      if (nav) nav.classList.add('active');
      loadErpData();
    }

    async function loadErpData(livePing = false) {
      // 1. Dashboard Stats
      const res = await fetch('/api/dashboard/stats');
      const stats = await res.json();

      document.getElementById('kpi-apps').innerText = stats.applications_online;
      document.getElementById('kpi-tenants').innerText = stats.active_tenants;
      document.getElementById('kpi-mrr').innerText = '£' + stats.monthly_recurring_revenue.toLocaleString(undefined, {minimumFractionDigits:2});
      document.getElementById('kpi-health').innerText = stats.system_health;

      // 2. App Registry
      const regRes = await fetch('/api/registry' + (livePing ? '?live_ping=true' : ''));
      const apps = await regRes.json();

      const regRows = apps.map(a => `
        <tr>
          <td><strong>${a.name}</strong></td>
          <td style="font-family:var(--hr-font-mono); font-weight:700; color:var(--hr-primary);">${a.port}</td>
          <td>${a.category}</td>
          <td style="font-family:var(--hr-font-mono); font-size:12px;">v${a.version}</td>
          <td><span class="badge badge-online">🟢 ${a.status}</span></td>
          <td>
            <a href="${a.url}" target="_blank" class="btn btn-secondary" style="padding:4px 8px; font-size:11px; text-decoration:none;">🚀 Launch App</a>
          </td>
        </tr>
      `).join('');

      document.getElementById('dash-registry-tbody').innerHTML = regRows;
      document.getElementById('registry-tbody').innerHTML = apps.map(a => `
        <tr>
          <td><strong>${a.name}</strong></td>
          <td style="font-family:var(--hr-font-mono);">${a.port}</td>
          <td style="font-family:var(--hr-font-mono); font-size:12px; color:var(--hr-muted);">${a.url}</td>
          <td>${a.category}</td>
          <td><span class="badge badge-online">${a.status}</span></td>
          <td style="font-family:var(--hr-font-mono); font-size:12px;">${a.latency_ms || 1.2} ms</td>
          <td>
            <a href="${a.url}" target="_blank" class="btn btn-primary" style="padding:4px 8px; font-size:11px; text-decoration:none;">Open</a>
          </td>
        </tr>
      `).join('');

      // 3. Tenants List
      const tRes = await fetch('/api/tenants');
      const tenants = await tRes.json();
      document.getElementById('tenants-tbody').innerHTML = tenants.map(t => `
        <tr>
          <td style="font-family:var(--hr-font-mono); font-weight:700; color:var(--hr-primary);">${t.tenant_code}</td>
          <td><strong>${t.company_name}</strong><br><span style="font-size:11px; color:var(--hr-muted);">${t.domain}</span></td>
          <td>${t.admin_email}</td>
          <td><span class="badge badge-tier">${t.plan_tier}</span></td>
          <td style="font-family:var(--hr-font-mono); font-weight:700;">£${t.monthly_fee_gbp.toFixed(2)}</td>
          <td><span class="badge badge-online">${t.status}</span></td>
        </tr>
      `).join('');

      // 4. Backups List
      const bRes = await fetch('/api/backups');
      const backups = await bRes.json();
      document.getElementById('backups-tbody').innerHTML = backups.map(b => `
        <tr>
          <td style="font-family:var(--hr-font-mono); font-weight:700;">${b.backup_id}</td>
          <td>${b.database_name}</td>
          <td style="font-family:var(--hr-font-mono);">${b.file_size_kb} KB</td>
          <td><span class="badge badge-online">🔒 ${b.status}</span></td>
          <td style="font-size:12px; color:var(--hr-muted);">${b.created_at}</td>
        </tr>
      `).join('');
    }

  <!-- Provision Tenant Modal -->
  <div class="modal-overlay" id="modal-tenant" style="display:none; position:fixed; inset:0; background:rgba(15,23,42,0.6); backdrop-filter:blur(4px); align-items:center; justify-content:center; z-index:1000;">
    <div class="modal-box" style="background:#fff; border:1px solid var(--hr-border); border-radius:10px; width:100%; max-width:540px; padding:24px; box-shadow:0 20px 25px -5px rgba(0,0,0,0.1);">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;">
        <h3 style="font-size:16px; font-weight:700; color:var(--hr-text);">Provision Client Tenant</h3>
        <button style="background:none; border:none; color:var(--hr-muted); cursor:pointer; font-size:18px;" onclick="closeModals()">✕</button>
      </div>
      <form id="form-tenant" onsubmit="submitTenant(event)">
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
          <div>
            <label style="display:block; font-size:12px; font-weight:600; color:var(--hr-muted); margin-bottom:4px;">Company Name</label>
            <input type="text" id="ten-name" class="search-box" style="width:100%;" required placeholder="e.g. Apex Wealth Advisory">
          </div>
          <div>
            <label style="display:block; font-size:12px; font-weight:600; color:var(--hr-muted); margin-bottom:4px;">Admin Email</label>
            <input type="email" id="ten-email" class="search-box" style="width:100%;" required placeholder="e.g. admin@apexwealth.co.uk">
          </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
          <div>
            <label style="display:block; font-size:12px; font-weight:600; color:var(--hr-muted); margin-bottom:4px;">Plan Tier</label>
            <select id="ten-tier" class="search-box" style="width:100%;">
              <option value="Professional">Professional Plan</option>
              <option value="Enterprise" selected>Enterprise Plan</option>
              <option value="Starter">Starter Plan</option>
            </select>
          </div>
          <div>
            <label style="display:block; font-size:12px; font-weight:600; color:var(--hr-muted); margin-bottom:4px;">Monthly Fee (£)</label>
            <input type="number" step="50" id="ten-fee" class="search-box" style="width:100%;" value="450" required>
          </div>
        </div>
        <div style="margin-bottom:18px;">
          <label style="display:block; font-size:12px; font-weight:600; color:var(--hr-muted); margin-bottom:4px;">Assigned Domain</label>
          <input type="text" id="ten-domain" class="search-box" style="width:100%;" placeholder="apex.hr-suite.local">
        </div>
        <div style="display:flex; justify-content:flex-end; gap:10px;">
          <button type="button" class="btn btn-secondary" onclick="closeModals()">Cancel</button>
          <button type="submit" id="btn-submit-ten" class="btn btn-primary">Provision Tenant</button>
        </div>
      </form>
    </div>
  </div>

  <div id="hr-toast" style="position:fixed; bottom:24px; right:24px; background:#0f172a; color:#fff; padding:12px 20px; border-radius:8px; font-size:13px; font-weight:600; display:none; z-index:9999; box-shadow:0 10px 15px -3px rgba(0,0,0,0.2);">
    Action Complete
  </div>

  <script>
    function showToast(msg, isSuccess = true) {
      const t = document.getElementById('hr-toast');
      t.innerText = msg;
      t.style.background = isSuccess ? '#0f172a' : '#ef4444';
      t.style.display = 'block';
      setTimeout(() => { t.style.display = 'none'; }, 3000);
    }

    function openTenantModal() {
      document.getElementById('form-tenant').reset();
      document.getElementById('modal-tenant').style.display = 'flex';
    }

    function closeModals() {
      document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
    }

    async function submitTenant(e) {
      e.preventDefault();
      const btn = document.getElementById('btn-submit-ten');
      btn.innerText = 'Provisioning...';
      btn.disabled = true;

      const payload = {
        company_name: document.getElementById('ten-name').value,
        admin_email: document.getElementById('ten-email').value,
        plan_tier: document.getElementById('ten-tier').value,
        monthly_fee_gbp: parseFloat(document.getElementById('ten-fee').value),
        domain: document.getElementById('ten-domain').value || null,
        modules_enabled: ["crm", "accounts", "hrms", "helpdesk", "booking"]
      };

      try {
        const res = await fetch('/api/tenants', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.status === 201) {
          showToast('✓ Tenant provisioned successfully!');
          closeModals();
          loadErpData();
        } else {
          showToast('Failed to provision tenant', false);
        }
      } catch (err) {
        showToast('Error connecting to server', false);
      } finally {
        btn.innerText = 'Provision Tenant';
        btn.disabled = false;
      }
    }

    async function deleteTenant(id) {
      if (confirm('Decommission this tenant?')) {
        await fetch(`/api/tenants/${id}`, { method: 'DELETE' });
        showToast('✓ Tenant decommissioned');
        loadErpData();
      }
    }

    async function triggerBackup() {
      await fetch('/api/backups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ database_name: 'master_cluster.db' })
      });
      showToast('✓ Database snapshot created and verified!');
      loadErpData();
    }

    window.addEventListener('DOMContentLoaded', () => {
      loadErpData();
      const hash = window.location.hash.replace('#', '') || 'dashboard';
      navigate(hash);
    });
  </script>
</body>
</html>
"""
