# HR Business OS — V1 Backend Architecture

## Framework
- FastAPI, Python 3.12, Uvicorn ASGI
- Entrypoint: `src/app.py`
- Startup: `init_db()` seeds the 7-application HR Professional Services topology on first run

## Business Logic
- **MRR Computation**: `SUM(monthly_fee_gbp) WHERE status='Active'` executed fresh on every `/api/dashboard/stats` call
- **Tenant Provisioning**: Auto-generates `TEN-{random_5digit}` unique ID enforced by `UNIQUE` DB constraint
- **WAL Snapshot Trigger**: Creates a `BAK-{timestamp}` ledger entry; production deployment should execute `sqlite3 {db_path} ".backup {snapshot_path}"` for each registered application database

## Validation & Errors
- `404` on unknown tenant_id or backup_id
- `409` on duplicate tenant subdomain or email
- `422` on missing required provisioning fields
