# GEP OHS Workforce Management System

Complete workflow execution — Contract to Compliance to Cash — on Odoo 19 CE.

## Quick Start (Local Docker)

```bash
# Clone the repo
git clone https://github.com/deeprunnerai/workforce-management.git
cd workforce-management

# Start Odoo + PostgreSQL
cd docker
docker-compose up -d

# Wait ~30 seconds for startup
```

**Access Odoo:** http://localhost:8069

### First Time Setup

1. Create a new database:
   - **Database Name:** `wfm`
   - **Email:** `admin@example.com`
   - **Password:** `admin`
   - **Demo Data:** Check this box

2. Install the module:
   - Go to **Apps**
   - Click **Update Apps List** (in menu)
   - Remove "Apps" filter, search for `wfm`
   - Install **WFM Core**

### Useful Commands

```bash
# Start containers
docker-compose up -d

# View logs
docker-compose logs -f odoo

# Stop containers
docker-compose down

# Reset everything (delete data)
docker-compose down -v
```

## Team

| Dev | GitHub | Branch | Scope |
|-----|--------|--------|-------|
| **Dev A** | [@gauravdr](https://github.com/gauravdr) | `dev-a` | Core models, seed data |
| **Dev B** | [@riya-2098](https://github.com/riya-2098) | `dev-b` | Kanban, dashboard |
| **Dev C** | [@PanosAndr](https://github.com/PanosAndr) | `dev-c` | Portal, WhatsApp |

## Module Structure

```
addons/
└── wfm_core/          # Core models (Dev A)
    ├── models/
    │   ├── partner.py       # Client/Partner extension
    │   ├── installation.py  # Installation model
    │   ├── visit_stage.py   # Kanban stages
    │   └── visit.py         # Visit model
    ├── views/
    ├── data/
    ├── demo/
    └── security/
```

## Documentation

- [CLAUDE.md](CLAUDE.md) - Project context
- [PLAN.md](PLAN.md) - Implementation plan
- [TASKS.md](TASKS.md) - Task breakdown
- [STATUS.md](STATUS.md) - Progress tracking

## Links

- **Production:** https://odoo.deeprunner.ai
- **Confluence:** [Knowledge Base](https://deeprunner.atlassian.net/wiki/spaces/Product/pages/44793870)
