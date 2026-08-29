import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.database import get_db, init_db

def seed():
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM consolidation_metrics")
        cursor.execute("DELETE FROM tenants")
        cursor.execute("DELETE FROM modules")

        # Modules Catalog
        modules = [
            ("crm", "Lead & Deal Management", "Sales & Pipeline", "Enterprise CRM, Lead Scoring, Opportunity Stages"),
            ("selling", "Quotations & Sales Orders", "Sales & Invoicing", "Multi-Currency Quotations, Sales Invoices, Commission Schedules"),
            ("buying", "Supplier Purchasing & RFQs", "Procurement", "Purchase Orders, Supplier Ledger, Material Requests"),
            ("accounts", "General Ledger & Double-Entry Accounting", "Finance", "Chart of Accounts, Journal Entries, Balance Sheets, Profit & Loss"),
            ("stock", "Inventory & Warehouse Multi-Location", "Supply Chain", "Stock Levels, Serial Number Tracking, Automated Low-Stock Reordering"),
            ("hrms", "People Operations & Leave Management", "Human Resources", "Employee Master, Leave Approvals, Attendance Tracking"),
            ("helpdesk", "Omnichannel Ticket Support", "Customer Support", "SLA Escalation Clocks, Knowledge Base, Customer Self-Service"),
            ("projects", "Gantt Milestone & Timesheet Tracking", "Operations", "Project Costing, Timesheet Logging, Billable Hours")
        ]
        for m in modules:
            cursor.execute("INSERT INTO modules (module_key, name, category, description, is_installed) VALUES (?, ?, ?, ?, 1)", m)

        # Tenants
        tenants = [
            ("TNT-APEX01", "Apex Logistics Ltd", "ops@apexlogistics.co.uk", "Enterprise", "apex.hr-services.local", "Active", json.dumps(["crm", "accounts", "stock", "buying"])),
            ("TNT-VANG02", "Vanguard Wealth Management", "director@vanguard.ch", "Enterprise", "vanguard.hr-services.local", "Active", json.dumps(["crm", "accounts", "hrms", "helpdesk"])),
            ("TNT-VORT03", "Vortex Digital Agency", "hello@vortexagency.io", "Standard", "vortex.hr-services.local", "Active", json.dumps(["crm", "selling", "projects", "accounts"]))
        ]
        for t in tenants:
            cursor.execute("""
            INSERT INTO tenants (tenant_code, company_name, admin_email, plan_tier, domain, status, modules_enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, t)

        # Multi-Entity Financial Metrics
        cursor.execute("""
        INSERT INTO consolidation_metrics (period, total_revenue, total_expenses, net_profit, headcount)
        VALUES ('2026-Q3', 385000.0, 142000.0, 243000.0, 48)
        """)

        conn.commit()
    print("✅ HR Business OS / ERP demo dataset seeded successfully!")

if __name__ == "__main__":
    seed()
