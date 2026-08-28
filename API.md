# HR Business OS — V1 API Specification

## Overview
- **Service Name**: HR Business OS (Control Plane)
- **Port**: 8008
- **Status**: 🔒 V1 Locked

---

## Endpoint Reference

### 1. System
#### `GET /api/health`
**Response**: `{"status": "healthy", "service": "HR Business OS", "version": "2.0.0"}`

#### `GET /api/branding`
**Response**: Brand tokens + Business OS product identity

---

### 2. Control Plane Metrics
#### `GET /api/dashboard/stats`
**Description**: Returns top-level control plane KPIs: active tenants, MRR (GBP), registered applications, and system status.
**Response**:
```json
{
  "active_tenants": 5,
  "monthly_recurring_revenue_gbp": 1770.0,
  "registered_apps": 7,
  "system_status": "All Systems Operational",
  "total_backups": 3
}
```

---

### 3. Application Registry
#### `GET /api/registry`
**Description**: Returns the 7-application HR Professional Services topology with ports, health URLs, and status.
**Response**:
```json
[
  {"id": 1, "name": "HR CRM", "port": 8001, "url": "http://localhost:8001", "status": "Running"},
  {"id": 2, "name": "HR Bookings", "port": 8002, "url": "http://localhost:8002", "status": "Running"},
  {"id": 3, "name": "HR Accounts", "port": 8004, "url": "http://localhost:8004", "status": "Running"},
  {"id": 4, "name": "HR People", "port": 8005, "url": "http://localhost:8005", "status": "Running"},
  {"id": 5, "name": "HR Helpdesk", "port": 8006, "url": "http://localhost:8006", "status": "Running"},
  {"id": 6, "name": "HR Client Portal", "port": 8009, "url": "http://localhost:8009", "status": "Running"},
  {"id": 7, "name": "HR Business OS", "port": 8008, "url": "http://localhost:8008", "status": "Running"}
]
```

---

### 4. Tenant Management
#### `GET /api/tenants`
**Description**: Lists all provisioned client tenants with their subscription plan and MRR contribution.
**Response**: Array of Tenant objects

#### `POST /api/tenants`
**Description**: Provisions a new client tenant with plan tier and fee assignment.
**Request Body**:
```json
{
  "company_name": "Apex Manufacturing Group Ltd",
  "contact_email": "it@apex-manufacturing.co.uk",
  "plan_tier": "Professional",
  "monthly_fee_gbp": 450.0,
  "subdomain": "apex-manufacturing"
}
```
**Response**: `201 Created` (`{"id": 6, "tenant_id": "TEN-8024", "status": "Active"}`)

#### `PATCH /api/tenants/{id}/status`
**Description**: Activates or suspends a tenant account.
**Request Body**: `{"status": "Suspended", "reason": "Payment overdue"}`
**Response**: `200 OK`

---

### 5. Backups & WAL Snapshots
#### `GET /api/backups`
**Description**: Lists all recorded SQLite WAL snapshots with timestamp, file reference, and verification status.
**Response**: Array of Backup objects

#### `POST /api/backups`
**Description**: Triggers a new SQLite WAL snapshot across all application databases. Records the snapshot in the control plane.
**Request Body**: `{"notes": "Pre-deployment baseline snapshot"}`
**Response**: `201 Created` (`{"id": 4, "snapshot_id": "BAK-1787878024", "status": "Verified"}`)

---

### 6. Data Sovereignty
#### `GET /api/export/csv` — Tenant and control plane export
#### `GET /api/export/json` — Full control plane JSON export
