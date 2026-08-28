# HR Business OS — V1 Development Guide

## Local Setup
```bash
cd products/hemanth-ranam-erp
pip install fastapi uvicorn pydantic httpx pytest
python3 -m uvicorn src.app:app --host 127.0.0.1 --port 8008 --reload
```

## Run E2E Tests
```bash
python3 scripts/e2e_qa_test.py
```
Expected:
```
✅ [1/7] Health & Institutional Branding verified.
✅ [2/7] Application registry verified: 7 applications registered.
✅ [3/7] Tenant provisioned: TEN-XXXXX (Status: Active).
✅ [4/7] Database snapshot created.
✅ [5/7] Control plane metrics calculated (Active Tenants: 5, MRR: £1,770.00).
✅ [6/7] Multi-tenant subscription roster queried.
✅ [7/7] CSV and JSON data sovereignty exports verified.
🎉 ALL REAL-WORLD HR BUSINESS OS QA TESTS PASSED WITH 100% SUCCESS!
```
