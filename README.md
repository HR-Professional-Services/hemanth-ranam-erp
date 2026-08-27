# Hemanth Ranam — ERP & Business OS Implementation Blueprint

Enterprise Resource Planning (ERP) & unified business operations OS built on Frappe & ERPNext v14/v15.

---

## 💼 Modules Covered
* **Financial Accounting & Invoicing**: General ledger, multi-currency accounts, tax templates, automated billing.
* **Buying & Selling**: Quotes, sales orders, purchase receipts, supplier management.
* **Stock & Inventory**: Multi-warehouse tracking, batch management, serialized assets, automated reordering.
* **Project Management & Manufacturing**: Gantt charts, work orders, BOM creation, time tracking.

---

## 🏛️ Deployment Architecture
* **Framework**: Frappe Framework (Python 3.11/3.12 + MariaDB 10.6+ + Redis)
* **Hosting**: Frappe Cloud or Dedicated Ubuntu VPS with Bench CLI
* **Edge Proxy**: Cloudflare DNS + SSL proxy (`erp.clientdomain.com`)

**Author**: Hemanth Ranam  
**Website**: [https://app.hemanth-ranam.workers.dev/](https://app.hemanth-ranam.workers.dev/)
