# HR Business OS — V1 Database Schema

## Storage Architecture
- **Engine**: SQLite 3 WAL
- **Default Database File**: `erp.db`

---

## Table DDL

### 1. `applications` (HR Suite Registry)
```sql
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    port INTEGER UNIQUE NOT NULL,
    url TEXT NOT NULL,
    health_url TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'Running',  -- Running|Stopped|Error|Maintenance
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. `tenants` (Client Subscriptions)
```sql
CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT UNIQUE NOT NULL,               -- Format: TEN-NNNNN
    company_name TEXT NOT NULL,
    contact_email TEXT UNIQUE NOT NULL,
    plan_tier TEXT DEFAULT 'Starter',              -- Starter|Professional|Enterprise
    monthly_fee_gbp REAL NOT NULL DEFAULT 0.0,
    status TEXT DEFAULT 'Active',                  -- Active|Suspended|Cancelled
    subdomain TEXT UNIQUE,
    provisioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. `backups` (Snapshot Ledger)
```sql
CREATE TABLE IF NOT EXISTS backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id TEXT UNIQUE NOT NULL,   -- Format: BAK-XXXXXXXXX
    databases_included TEXT NOT NULL,   -- JSON array of DB paths snapshotted
    file_reference TEXT,
    status TEXT DEFAULT 'Verified',      -- Pending|Verified|Failed
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Seed Data
On initialization, the `applications` table is populated with the full 7-application HR Professional Services topology (ports 8001–8009).

## MRR Calculation
```
monthly_recurring_revenue_gbp = SUM(monthly_fee_gbp) WHERE status = 'Active'
```
