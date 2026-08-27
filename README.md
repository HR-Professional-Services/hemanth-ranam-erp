# HR Business OS / ERP — Hemanth Ranam Professional Services

[![CI](https://github.com/HR-Professional-Services/hemanth-ranam-erp/actions/workflows/ci.yml/badge.svg)](https://github.com/HR-Professional-Services/hemanth-ranam-erp/actions)
[![License: GPL-3.0 / MIT](https://img.shields.io/badge/License-GPL--3.0%20%2F%20MIT-blue.svg)](LICENSE-COMPLIANCE.md)
[![Zero Monthly Cost](https://img.shields.io/badge/Hosting-Zero--Cost%20Tier-success.svg)](DEPLOYMENT.md)

> **"All-in-one small-business operating system and enterprise resource planning control plane with zero per-seat licensing fees."**

---

## 🌟 Executive Overview
**HR Business OS / ERP** is an institutional enterprise operating system and multi-tenant control plane engineered by **Hemanth Ranam Professional Services**. Built for growing mid-sized enterprises, trading groups, logistics firms, and holding companies, it replaces expensive ERP subscriptions like NetSuite, SAP Business One, or Odoo Enterprise ($100–$250/user/mo) with a unified, self-hosted Frappe Framework & ERPNext architecture.

---

## 💼 Core Business Capabilities
* **Unified Business Modules**: Seamlessly integrated CRM, Double-Entry Accounting, Inventory & Multi-Warehouse Stock, HRMS, Omnichannel Helpdesk, Purchasing, and Project Costing.
* **Multi-Tenant Control Plane**: Provision separate tenant environments for client companies, subsidiaries, or distinct operating branches.
* **Consolidated Financial Intelligence**: Real-time roll-up of multi-company revenue, expenses, and net operating margins.
* **Turnkey Provisioning API**: Automated site generation (`POST /api/provision-site`) with Hemanth Ranam white-label design tokens.
* **100% Client Data Sovereignty**: 1-click CSV & JSON complete database export with zero vendor lock-in.

---

## 🎨 White-Label Branding
Configure brand identity, module catalog, and default editions in `src/branding.json`.

---

## 🚀 Quickstart Installation
```bash
# 1. Clone repository
git clone https://github.com/HR-Professional-Services/hemanth-ranam-erp.git
cd hemanth-ranam-erp

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed demo tenants & enterprise modules
python scripts/seed_demo_data.py

# 4. Start control plane server
uvicorn src.app:app --reload --port 8000
```
Open [http://localhost:8000](http://localhost:8000) for the Business OS & ERP Control Plane.

---

## 🐳 Docker Deployment
```bash
docker build -t hemanth-ranam-erp .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data --name hr-erp hemanth-ranam-erp
```

---

## 📦 Client Handover Suite
* [CLIENT-ONBOARDING.md](client/CLIENT-ONBOARDING.md)
* [SETUP-CHECKLIST.md](client/SETUP-CHECKLIST.md)
* [HANDOVER.md](client/HANDOVER.md)
* [ADMIN-GUIDE.md](client/ADMIN-GUIDE.md)
* [USER-GUIDE.md](client/USER-GUIDE.md)
* [TRAINING.md](client/TRAINING.md)
* [SUPPORT.md](client/SUPPORT.md)

---

## 🏛️ Commercial Services
**Hemanth Ranam Professional Services**  
* **Live Hub**: [https://app.hemanth-ranam.workers.dev/](https://app.hemanth-ranam.workers.dev/)  
* **Direct Inquiry**: [hemanth.ranam@gmail.com](mailto:hemanth.ranam@gmail.com) | WhatsApp: `+91 7675815245`
