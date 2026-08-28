# HR Business OS — V1 Deployment Guide

## System Requirements
- **Runtime**: Python 3.10+
- **Port**: `8008`

## Environment Variables
| Variable | Default | Description |
| :--- | :--- | :--- |
| `PORT` | `8008` | Uvicorn port |
| `ERP_DB_PATH` | `erp.db` | SQLite database path |

## Startup Commands
```bash
# Development
python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8008 --reload

# Production
python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8008 --workers 2
```

## Health Check
```bash
curl http://127.0.0.1:8008/api/health
```

## Backup
```bash
sqlite3 erp.db ".backup 'erp_snapshot_$(date +%Y%m%d).db'"
curl -s http://127.0.0.1:8008/api/export/json > erp_backup.json
```
