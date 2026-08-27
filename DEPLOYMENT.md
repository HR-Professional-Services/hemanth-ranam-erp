# DEPLOYMENT GUIDE — HR BUSINESS OS / ERP

**System**: HR Business OS / ERP (Product 08)  
**Provider**: Hemanth Ranam Professional Services  
**Source Hub**: [https://app.hemanth-ranam.workers.dev/](https://app.hemanth-ranam.workers.dev/)

---

## 1. Hosting Classifications
* **Tier A**: Dockerized Multi-Tenant Frappe Bench on Ubuntu VPS ($10.00 - $20.00/mo).
* **Tier B**: Frappe Cloud Dedicated Site with Automated Backups.
* **Tier C**: Local On-Premise Air-Gapped Microserver ($0.00 recurring).

---

## 2. Docker Quickstart
```bash
git clone https://github.com/HR-Professional-Services/hemanth-ranam-erp.git
cd hemanth-ranam-erp
docker compose up -d --build
```
