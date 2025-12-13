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

2. Install the modules:
   - Go to **Apps**
   - Click **Update Apps List** (in menu)
   - Remove "Apps" filter, search for `wfm`
   - Install **WFM Core**, **WFM FSM**, **WFM Portal**, **WFM WhatsApp**, **WFM AI Chat**

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

## Modules

| Module | Version | Description |
|--------|---------|-------------|
| `wfm_core` | 19.0.2.1.0 | Core models, SEPE exports, billing, workflows |
| `wfm_fsm` | 19.0.4.0.0 | Kanban, dashboard, Smart Assignment, Churn Analysis |
| `wfm_portal` | 19.0.1.0.0 | Partner self-service portal |
| `wfm_whatsapp` | 19.0.1.0.0 | WhatsApp notifications via Twilio |
| `wfm_ai_chat` | 19.0.1.0.0 | AI Chat integration with LLM tools |

## Features

- **Visit Management** - Full lifecycle from draft to completed
- **Smart Assignment** - AI-powered partner recommendations
- **Partner Churn Analysis** - Risk scoring and retention tools
- **WhatsApp Integration** - Automated notifications via Twilio
- **AI Chat** - Natural language interface for system queries
- **Autonomous Workflows** - Trigger-based automation engine
- **SEPE Exports** - Government compliance reporting
- **Billing Dashboard** - Visit billing status tracking

## Menu Structure

```
Workforce Management
├── Visits
├── Partners
├── Clients
├── Reporting
│   └── SEPE
├── Billing
├── Analysis
│   ├── Partner Retention
│   └── Churn Analytics
├── Automation
│   ├── Workflows
│   └── Execution Logs
└── Config
```

## Team

| Dev | GitHub | Branch | Scope |
|-----|--------|--------|-------|
| **Dev A** | [@gauravdr](https://github.com/gauravdr) | `dev-a` | Core models, AI Chat, Workflows |
| **Dev B** | [@riya-2098](https://github.com/riya-2098) | `dev-b` | Kanban, dashboard |
| **Dev C** | [@PanosAndr](https://github.com/PanosAndr) | `dev-c` | Portal, WhatsApp, SEPE |

## Documentation

- [CLAUDE.md](CLAUDE.md) - Project context for AI
- [MODULES.md](MODULES.md) - Module documentation
- [SKILLS.md](SKILLS.md) - System capabilities
- [STATUS.md](STATUS.md) - Progress tracking
- [TASKS.md](TASKS.md) - Task breakdown
- [CHANGELOG.md](CHANGELOG.md) - Version history

## Links

- **Production:** https://odoo.deeprunner.ai
- **Confluence:** [Knowledge Base](https://deeprunner.atlassian.net/wiki/spaces/Product/pages/44793870)
