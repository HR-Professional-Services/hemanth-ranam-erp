# HR Business OS — V1 Security Policy

## Implemented Controls
- SQL injection defense via parameterized `?` placeholders throughout
- Tenant ID uniqueness enforced at DB constraint level (`UNIQUE` on `tenant_id`)
- Application registry is bootstrapped at startup and is not modifiable via external API calls in V1

## Future (V2)
- Admin authentication required for control plane access
- Tenant-level API key issuance
- Role separation: `Platform Admin` vs `Billing Admin` vs `Read-Only Viewer`
- Audit log for all provisioning and suspension events
