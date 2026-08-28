# HR Business OS — V1 Frontend Architecture

## Design System & Theme
- **Theme**: Pure Light Mode (`#F8FAFC` canvas, `#FFFFFF` cards)
- **Primary**: `#2563EB`

## SPA Views (5 Active)
1. **`view-dashboard`**: Live control plane KPIs (Active Tenants, MRR £, Registered Apps), 7-microservice topology grid with direct launch links
2. **`view-registry`**: Application registry table — name, port, URL, status badge, direct open link
3. **`view-tenants`**: Tenant subscription roster with plan tier, MRR contribution, Provision Tenant modal
4. **`view-backups`**: WAL snapshot ledger, Trigger Snapshot modal with notes field
5. **`view-reports`**: Consolidated MRR by plan tier, CSV/JSON export actions

## Modals (Outside `<script>`)
- `#modal-tenant`: Provision new client tenant — company, email, plan tier, monthly fee, subdomain
