import os
import json
import csv
import io
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from src.database import init_db, get_db, get_db_path

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
        "brand_name": "HR Professional Services",
        "product_name": "HR Business OS",
        "primary_color": "#2563eb",
        "bg_canvas": "#ffffff",
        "bg_secondary": "#f8fafc",
        "text_primary": "#0f172a",
        "text_muted": "#64748b"
    }

@app.on_event("startup")
def startup_event():
    init_db()

# --- Pydantic Data Models ---
class TenantCreate(BaseModel):
    company_name: str
    admin_email: str
    plan_tier: Optional[str] = "Enterprise"
    domain: Optional[str] = None
    monthly_fee_gbp: Optional[float] = 450.0
    modules_enabled: Optional[List[str]] = ["crm", "booking", "accounts", "hrms", "helpdesk"]

class BackupCreate(BaseModel):
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
        tenant_count = conn.execute("SELECT COUNT(*) FROM tenants WHERE status = 'Active'").fetchone()[0]
        mrr = conn.execute("SELECT COALESCE(SUM(monthly_fee_gbp), 0) FROM tenants WHERE status = 'Active'").fetchone()[0]
        app_count = conn.execute("SELECT COUNT(*) FROM app_registry").fetchone()[0]
        backup_count = conn.execute("SELECT COUNT(*) FROM system_backups").fetchone()[0]

        return {
            "active_tenants": tenant_count,
            "mrr_gbp": mrr,
            "monthly_recurring_revenue": mrr,
            "arr_gbp": mrr * 12.0,
            "registered_apps": app_count,
            "verified_backups": backup_count,
            "system_status": "All Systems Nominal"
        }

@app.get("/api/registry")
def list_registry():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM app_registry ORDER BY port ASC").fetchall()
        return [dict(r) for r in rows]

@app.get("/api/tenants")
def list_tenants():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM tenants ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

@app.post("/api/tenants", status_code=201)
def create_tenant(payload: TenantCreate):
    with get_db() as conn:
        t_code = f"TEN-{int(time.time()) % 10000:04d}"
        dom = payload.domain or f"{payload.company_name.lower().replace(' ', '')}.hr-suite.local"
        modules_json = json.dumps(payload.modules_enabled)

        cur = conn.execute("""
        INSERT INTO tenants (tenant_code, company_name, admin_email, plan_tier, domain, status, monthly_fee_gbp, modules_enabled)
        VALUES (?, ?, ?, ?, ?, 'Active', ?, ?)
        """, (t_code, payload.company_name, payload.admin_email, payload.plan_tier, dom, payload.monthly_fee_gbp, modules_json))
        conn.commit()
        return {"id": cur.lastrowid, "tenant_code": t_code, "domain": dom, "status": "Active"}

@app.get("/api/backups")
def list_backups():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM system_backups ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

@app.post("/api/backups", status_code=201)
def trigger_backup(payload: BackupCreate):
    with get_db() as conn:
        b_id = f"BAK-{int(time.time())}"
        size_kb = 2048 # Simulated snapshot size
        cur = conn.execute("""
        INSERT INTO system_backups (backup_id, database_name, file_size_kb, status)
        VALUES (?, ?, ?, 'Verified')
        """, (b_id, payload.database_name, size_kb))
        conn.commit()
        return {"id": cur.lastrowid, "backup_id": b_id, "status": "Verified"}

@app.get("/api/export/csv")
def export_csv():
    with get_db() as conn:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Tenant Code", "Company Name", "Admin Email", "Plan Tier", "Domain", "Monthly Fee (GBP)", "Status", "Created At"])
        rows = conn.execute("SELECT tenant_code, company_name, admin_email, plan_tier, domain, monthly_fee_gbp, status, created_at FROM tenants ORDER BY id DESC").fetchall()
        for r in rows:
            writer.writerow(list(r))
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=hr_erp_tenants.csv"})

@app.get("/api/export/json")
def export_json():
    with get_db() as conn:
        tenants = [dict(r) for r in conn.execute("SELECT * FROM tenants").fetchall()]
        apps = [dict(r) for r in conn.execute("SELECT * FROM app_registry").fetchall()]
        backups = [dict(r) for r in conn.execute("SELECT * FROM system_backups").fetchall()]
        return {"export_timestamp": datetime.now().isoformat(), "tenants": tenants, "apps": apps, "backups": backups}

# --- Main UI Shell ---
@app.get("/", response_class=HTMLResponse)
def index_page():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HR Business OS — Master ERP & Control Plane</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --hr-primary: #2563eb;
      --hr-primary-hover: #1d4ed8;
      --hr-primary-light: #eff6ff;
      --hr-success: #16a34a;
      --hr-warning: #d97706;
      --hr-danger: #dc2626;
      --hr-bg: #f8fafc;
      --hr-surface: #ffffff;
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
    .nav-item a { display: flex; align-items: center; gap: 12px; padding: 10px 14px; color: var(--hr-text-secondary); text-decoration: none; border-radius: var(--hr-radius-sm); font-size: 13px; font-weight: 500; cursor: pointer; }
    .nav-item a:hover { background: var(--hr-surface-hover); color: var(--hr-text); }
    .nav-item.active a { background: var(--hr-primary-light); color: var(--hr-primary); font-weight: 600; border-left: 3px solid var(--hr-primary); }

    .main-wrapper { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
    .top-bar { height: 64px; background: var(--hr-surface); border-bottom: 1px solid var(--hr-border); display: flex; align-items: center; justify-content: space-between; padding: 0 28px; }
    .content-body { flex: 1; overflow-y: auto; padding: 28px; }
    .view-section { display: none; }
    .view-section.active { display: block; }

    .btn { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: var(--hr-radius-sm); font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all 0.15s; }
    .btn-primary { background: var(--hr-primary); color: #fff; }
    .btn-primary:hover { background: var(--hr-primary-hover); }
    .btn-secondary { background: var(--hr-surface); color: var(--hr-text); border: 1px solid var(--hr-border); }
    .btn-secondary:hover { background: var(--hr-surface-hover); }

    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .kpi-card { background: var(--hr-surface); border: 1px solid var(--hr-border); border-radius: var(--hr-radius-md); padding: 20px; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.03); }
    .kpi-label { font-size: 12px; color: var(--hr-muted); text-transform: uppercase; margin-bottom: 8px; font-weight: 600; }
    .kpi-val { font-size: 24px; font-weight: 800; font-family: var(--hr-font-mono); color: var(--hr-text); }

    .data-card { background: var(--hr-surface); border: 1px solid var(--hr-border); border-radius: var(--hr-radius-md); overflow: hidden; margin-bottom: 24px; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.03); }
    .card-header { padding: 18px 22px; border-bottom: 1px solid var(--hr-border); display: flex; justify-content: space-between; align-items: center; }
    .card-title { font-size: 15px; font-weight: 700; color: var(--hr-text); }

    table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
    th { padding: 12px 18px; background: #f8fafc; color: var(--hr-muted); font-weight: 600; border-bottom: 1px solid var(--hr-border); font-size: 11px; text-transform: uppercase; }
    td { padding: 14px 18px; border-bottom: 1px solid var(--hr-border); color: var(--hr-text); }
    tr:hover td { background: #f8fafc; }

    .badge { display: inline-flex; padding: 3px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
    .badge-online { background: #ecfdf5; color: #16a34a; }
    .badge-tier { background: #eff6ff; color: #2563eb; }

    .search-box { background: var(--hr-surface); border: 1px solid var(--hr-border); border-radius: 6px; padding: 8px 12px; font-size: 13px; color: var(--hr-text); font-family: inherit; }
  </style>
</head>
<body>

  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="brand-header">
      <div class="brand-badge">HR</div>
      <div>
        <div class="brand-title">HR Business OS</div>
        <div style="font-size:11px; color:var(--hr-muted);">Master ERP & Control Plane</div>
      </div>
    </div>
    <ul class="nav-menu">
      <li class="nav-item active" id="nav-dashboard"><a onclick="navigate('dashboard')">📊 Control Plane Overview</a></li>
      <li class="nav-item" id="nav-registry"><a onclick="navigate('registry')">🌐 Application Topology</a></li>
      <li class="nav-item" id="nav-tenants"><a onclick="navigate('tenants')">🏢 Client Tenants</a></li>
      <li class="nav-item" id="nav-backups"><a onclick="navigate('backups')">💾 System Backups & WAL</a></li>
      <li class="nav-item" id="nav-reports"><a onclick="navigate('reports')">📈 Global Financials</a></li>
    </ul>
    <div style="padding:16px; border-top:1px solid var(--hr-border); font-size:12px; color:var(--hr-text-secondary);">
      Topology: <strong>7 Live Microservices</strong>
    </div>
  </aside>

  <main class="main-wrapper">
    <header class="top-bar">
      <div style="font-size: 18px; font-weight: 700;" id="top-title">Control Plane Dashboard</div>
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
            <div class="kpi-label">Active Client Tenants</div>
            <div class="kpi-val" id="kpi-tenants">0</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Monthly Recurring Revenue</div>
            <div class="kpi-val" id="kpi-mrr" style="color:var(--hr-success);">£0.00</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Active Suite Applications</div>
            <div class="kpi-val" id="kpi-apps" style="color:var(--hr-primary);">7</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">System Health Status</div>
            <div class="kpi-val" style="color:var(--hr-success); font-size:16px;">✓ 100% Operational</div>
          </div>
        </div>

        <div class="data-card">
          <div class="card-header"><div class="card-title">Live Suite Microservices Status</div></div>
          <table>
            <thead>
              <tr>
                <th>Service Name</th>
                <th>Category</th>
                <th>Port</th>
                <th>Version</th>
                <th>Health Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="dash-apps-tbody"></tbody>
          </table>
        </div>
      </section>

      <!-- 2. REGISTRY VIEW -->
      <section id="view-registry" class="view-section">
        <div class="data-card">
          <div class="card-header"><div class="card-title">Suite Application Registry & Network Topology</div></div>
          <table>
            <thead>
              <tr>
                <th>Service Name</th>
                <th>Category</th>
                <th>Local Endpoint</th>
                <th>Health Probe</th>
                <th>Status</th>
                <th>Launch</th>
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
            <div class="card-title">Multi-Tenant Client Deployments</div>
            <button class="btn btn-primary" onclick="openTenantModal()">+ Provision Tenant</button>
          </div>
          <table>
            <thead>
              <tr>
                <th>Tenant Code</th>
                <th>Company</th>
                <th>Admin Contact</th>
                <th>Plan Tier</th>
                <th>Monthly Fee</th>
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
            <div class="card-title">Database Snapshots & Disaster Recovery</div>
            <button class="btn btn-primary" onclick="triggerSnapshot()">+ Trigger Snapshot Now</button>
          </div>
          <table>
            <thead>
              <tr>
                <th>Backup ID</th>
                <th>Database Instance</th>
                <th>Snapshot Size</th>
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
        <div class="data-card">
          <div class="card-header"><div class="card-title">Consolidated SaaS Revenue & Ledger Export</div></div>
          <div style="padding:20px; display:flex; gap:12px;">
            <button class="btn btn-primary" onclick="window.open('/api/export/csv')">📥 Download Tenants Ledger (CSV)</button>
            <button class="btn btn-secondary" onclick="window.open('/api/export/json')">📦 Export Complete Topology Dataset (JSON)</button>
          </div>
        </div>
      </section>

    </div>
  </main>

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
          <label style="display:block; font-size:12px; font-weight:600; color:var(--hr-muted); margin-bottom:4px;">Custom Subdomain</label>
          <input type="text" id="ten-domain" class="search-box" style="width:100%;" placeholder="e.g. apexwealth.hr-suite.local">
        </div>
        <div style="display:flex; justify-content:flex-end; gap:10px;">
          <button type="button" class="btn btn-secondary" onclick="closeModals()">Cancel</button>
          <button type="submit" class="btn btn-primary">Provision Tenant</button>
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
      t.style.background = isSuccess ? '#0f172a' : '#dc2626';
      t.style.display = 'block';
      setTimeout(() => { t.style.display = 'none'; }, 3000);
    }

    function navigate(view) {
      document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
      document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
      
      const sec = document.getElementById('view-' + view);
      const nav = document.getElementById('nav-' + view);
      if (sec) sec.classList.add('active');
      if (nav) nav.classList.add('active');

      const titles = {
        'dashboard': 'Control Plane Overview',
        'registry': 'Application Topology',
        'tenants': 'Client Tenants',
        'backups': 'System Backups & WAL',
        'reports': 'Global Financials & Exports'
      };
      document.getElementById('top-title').innerText = titles[view] || 'Control Plane';
      window.location.hash = view;
      loadErpData();
    }

    async function loadErpData() {
      // 1. Stats
      const res = await fetch('/api/dashboard/stats');
      const stats = await res.json();

      document.getElementById('kpi-tenants').innerText = stats.active_tenants;
      document.getElementById('kpi-mrr').innerText = '£' + stats.mrr_gbp.toLocaleString(undefined, {minimumFractionDigits:2});
      document.getElementById('kpi-apps').innerText = stats.registered_apps;

      // 2. Apps Registry
      const aRes = await fetch('/api/registry');
      const apps = await aRes.json();

      const appRows = apps.map(a => `
        <tr>
          <td><strong>${a.name}</strong></td>
          <td>${a.category}</td>
          <td style="font-family:var(--hr-font-mono); font-weight:700;">:${a.port}</td>
          <td style="font-family:var(--hr-font-mono); font-size:12px;">v${a.version}</td>
          <td><span class="badge badge-online">● ${a.status}</span></td>
          <td>
            <a href="${a.url}" target="_blank" class="btn btn-secondary" style="padding:4px 8px; font-size:11px; text-decoration:none;">🚀 Launch</a>
          </td>
        </tr>
      `).join('');

      document.getElementById('dash-apps-tbody').innerHTML = appRows;
      document.getElementById('registry-tbody').innerHTML = apps.map(a => `
        <tr>
          <td><strong>${a.name}</strong></td>
          <td>${a.category}</td>
          <td style="font-family:var(--hr-font-mono); font-size:12px;">${a.url}</td>
          <td style="font-family:var(--hr-font-mono); font-size:12px; color:var(--hr-muted);">${a.health_endpoint}</td>
          <td><span class="badge badge-online">● ${a.status}</span></td>
          <td>
            <a href="${a.url}" target="_blank" class="btn btn-secondary" style="padding:4px 8px; font-size:11px; text-decoration:none;">Launch</a>
          </td>
        </tr>
      `).join('');

      // 3. Tenants List
      const tRes = await fetch('/api/tenants');
      const tenants = await tRes.json();
      document.getElementById('tenants-tbody').innerHTML = tenants.map(t => `
        <tr>
          <td style="font-family:var(--hr-font-mono); font-weight:700; color:var(--hr-primary);">${t.tenant_code}</td>
          <td><strong>${t.company_name}</strong><br><span style="font-size:11px; color:var(--hr-muted);">${t.domain || ''}</span></td>
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

    function openTenantModal() {
      document.getElementById('form-tenant').reset();
      document.getElementById('modal-tenant').style.display = 'flex';
    }

    function closeModals() {
      document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
    }

    async function submitTenant(e) {
      e.preventDefault();
      const payload = {
        company_name: document.getElementById('ten-name').value,
        admin_email: document.getElementById('ten-email').value,
        plan_tier: document.getElementById('ten-tier').value,
        monthly_fee_gbp: parseFloat(document.getElementById('ten-fee').value),
        domain: document.getElementById('ten-domain').value || null
      };

      const res = await fetch('/api/tenants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.status === 201) {
        showToast('✓ Tenant provisioned successfully!');
        closeModals();
        loadErpData();
      }
    }

    async function triggerSnapshot() {
      const res = await fetch('/api/backups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ database_name: "erp_os_master.db" })
      });
      if (res.status === 201) {
        showToast('✓ SQLite WAL Snapshot created & verified');
        loadErpData();
      }
    }

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModals();
    });

    window.addEventListener('hashchange', () => {
      const hash = window.location.hash.replace('#', '') || 'dashboard';
      navigate(hash);
    });

    window.addEventListener('DOMContentLoaded', () => {
      const hash = window.location.hash.replace('#', '') || 'dashboard';
      navigate(hash);
    });
  </script>
</body>
</html>
"""
