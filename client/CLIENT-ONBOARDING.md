# CLIENT ONBOARDING & PROVISIONING GUIDE — HR BUSINESS OS / ERP

## 1. Enterprise Scope Gathering
* **Operating Companies & Legal Entities**:
* **Primary Currencies & Fiscal Year**:
* **Chart of Accounts Standard**: (Standard UK GAAP, US GAAP, IFRS)
* **Required Enterprise Modules**:
  - [x] CRM & Lead Pipeline
  - [x] Double-Entry Accounting & Ledger
  - [x] Warehouse Inventory & Stock
  - [x] HRMS & Leave Management
  - [x] Helpdesk & Customer Support
  - [x] Project Costing & Timesheets

---

## 2. Multi-Tenant Site Provisioning
Admins can provision new client sites by calling:
```bash
POST /api/tenants
Content-Type: application/json

{
  "company_name": "Horizon Quant Capital",
  "admin_email": "ops@horizonquant.com",
  "plan_tier": "Enterprise",
  "domain": "horizon.hemanth-ranam.com",
  "modules": ["crm", "accounts", "hrms", "helpdesk"]
}
```
