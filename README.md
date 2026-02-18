# Institutional IT Asset Inventory System — Phase 1

## Stack
- Python 3.12+
- Django 5.x
- PostgreSQL
- Django Templates + HTMX
- Tailwind-ready styling scaffold (Phase 1 uses static CSS with project palette)

## Tailwind note (Phase 1)
This phase ships a minimal CSS scaffold under `static/css/app.css` using the requested palette.
The template/layout structure is ready to plug in Tailwind CLI in Phase 5 without rewriting HTML.

## Docker local run
```bash
cp .env.example .env
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_core
docker compose exec web python manage.py seed_demo
```
> Note: `.env.example` uses `POSTGRES_HOST=localhost` for host-machine runs; Docker web service overrides it to `db`.

Open: http://localhost:8000

## Non-Docker local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Create PostgreSQL DB/user:
```sql
CREATE DATABASE inventory_db;
CREATE USER inventory_user WITH PASSWORD 'inventory_pass';
GRANT ALL PRIVILEGES ON DATABASE inventory_db TO inventory_user;
```
Export env vars (or keep `.env`):
```bash
export DJANGO_SETTINGS_MODULE=config.settings.dev
export DJANGO_SECRET_KEY=change-me-in-dev
export DJANGO_DEBUG=True
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
export POSTGRES_DB=inventory_db
export POSTGRES_USER=inventory_user
export POSTGRES_PASSWORD=inventory_pass
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
```
Then run:
```bash
python manage.py migrate
python manage.py seed_core
python manage.py seed_demo
python manage.py runserver
```

### Windows PowerShell quick check
If you see `OperationalError: [Errno 11001] getaddrinfo failed`, verify your shell is using:
```powershell
$env:POSTGRES_HOST = "localhost"
```
(That error usually means `POSTGRES_HOST=db` was used outside Docker.)

## Demo users (dev only)
- admin / Admin123!
- tech / Tech123!
- viewer / Viewer123!

## Phase 6 scope
- M7 Operations: maintenance, replacement, and decommission records with admin/technician forms.
- M8 Consumables: items + movement kardex with stock guardrails (no egress above stock).
- M9 Reports: safe asset report view + CSV export exposing only non-sensitive fields and indicators.
- Dashboard expanded with operations and low-stock metrics.
