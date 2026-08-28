# HR Business OS — V1 Frontend, Backend, Deployment, Security, Testing & Master V1 Doc

---

## FRONTEND.md

### Design System & Theme
- **Theme**: Pure Light Mode (`#F8FAFC` canvas, `#FFFFFF` cards)
- **Primary**: `#2563EB`

### SPA Views (5 Active)
1. **`view-dashboard`**: Live control plane KPIs (Active Tenants, MRR, Registered Apps), 7-microservice topology grid with direct launch links
2. **`view-registry`**: Application registry table — name, port, URL, status badge, direct open link
3. **`view-tenants`**: Tenant roster with plan tier, MRR contribution, Provision Tenant modal
4. **`view-backups`**: Snapshot ledger, Trigger Snapshot modal with notes field
5. **`view-reports`**: Consolidated MRR by plan tier, CSV/JSON export

### Modals (Outside `<script>`)
- `#modal-tenant`: Provision new client tenant — company, email, plan tier, monthly fee, subdomain

---

## BACKEND.md

### Framework
- FastAPI, Python 3.12, Uvicorn ASGI
- Entrypoint: `src/app.py`
- Startup: `init_db()` seeds 7-application registry on first run

### Business Logic
- **MRR Computation**: `SUM(monthly_fee_gbp) WHERE status='Active'` on every dashboard stats fetch
- **Tenant Provisioning**: Auto-generates `TEN-{random_5digit}` unique ID with `UNIQUE` constraint
- **WAL Snapshot Trigger**: Generates `BAK-{timestamp}` record; in production would execute `sqlite3 db_path ".backup ..."` for each registered app DB

---

## DEPLOYMENT.md

### Startup Commands
```bash
# Development
python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8008 --reload

# Production
python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8008 --workers 2
```

### Health Check
```bash
curl http://127.0.0.1:8008/api/health
```

### Environment Variables
| Variable | Default | Description |
| :--- | :--- | :--- |
| `PORT` | `8008` | Uvicorn port |
| `ERP_DB_PATH` | `erp.db` | SQLite database path |

---

## SECURITY.md

### Implemented Controls
- SQL injection defense via parameterized queries
- Tenant ID uniqueness enforced at DB constraint level
- Application registry is read-only from external callers in V1 (modifications via control plane only)

### Future (V2)
- Admin authentication for the control plane
- Tenant-level API key issuance
- Audit log for all provisioning and suspension events

---

## TESTING.md

### Test Summary
- **Total Scenarios**: 7 | **Pass Rate**: 100% (7/7) | **Status**: 🔒 Verified Baseline

| Step | Test | Result |
| :--- | :--- | :--- |
| **01** | Health & Branding | ✅ PASSED |
| **02** | Application Registry (7 apps, ports 8001–8009) | ✅ PASSED |
| **03** | Tenant Provisioning | ✅ PASSED |
| **04** | WAL Snapshot Trigger | ✅ PASSED |
| **05** | Control Plane MRR Metrics | ✅ PASSED |
| **06** | Multi-tenant Subscription Roster | ✅ PASSED |
| **07** | Data Sovereignty Exports | ✅ PASSED |

---

## HR-PROFESSIONAL-SERVICES-V1.md

### Baseline
- **Product**: HR Business OS
- **Repository**: `hemanth-ranam-erp`
- **Port**: `8008`
- **Version**: `1.0.0` | **Status**: 🔒 FINAL / LOCKED BASELINE

### Purpose
HR Business OS is the central control plane for the HR Professional Services suite. It provides the operational command centre: application topology visibility, client tenant provisioning, subscription management, WAL backup orchestration, and consolidated MRR reporting.

### Architecture Note
This is NOT a generic CRUD application. It is an infrastructure control layer. Future additions should extend the monitoring, alerting, or tenant management capabilities — not add unrelated business modules.

### Architecture Freeze
Port `8008`, the application registry topology (ports 8001–8009), and the tenant provisioning model are locked at V1.
