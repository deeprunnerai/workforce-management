# WFM Odoo Modules

Complete list of custom Odoo 19 modules developed for the GEP OHS Workforce Management System.

## Module Overview

| Module | Version | Status | Description |
|--------|---------|--------|-------------|
| `wfm_core` | 19.0.2.1.0 | Production | Core models, SEPE, billing, workflows |
| `wfm_fsm` | 19.0.4.0.0 | Production | Dashboard, Smart Assignment, Churn Analysis |
| `wfm_portal` | 19.0.1.0.0 | Production | Partner self-service backend |
| `wfm_whatsapp` | 19.0.1.0.0 | Production | Twilio WhatsApp integration |
| `wfm_ai_chat` | 19.0.1.0.0 | Production | AI Chat with LLM tools |
| `web_timeline` | 19.0.1.0.0 | Production | OCA Timeline view (dependency) |

## Dependency Graph

```
                    ┌──────────────┐
                    │   wfm_core   │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  wfm_fsm   │  │ wfm_portal │  │wfm_ai_chat │
    └──────┬─────┘  └────────────┘  └────────────┘
           │
           ▼
    ┌────────────────┐
    │  wfm_whatsapp  │
    └────────────────┘
```

---

## wfm_core - Core Module

**Purpose:** Foundation data models for the WFM system.

### Models

| Model | Description | Key Fields |
|-------|-------------|------------|
| `res.partner` (ext) | Extended with WFM flags | `is_wfm_client`, `is_wfm_partner`, `specialty`, `hourly_rate` |
| `wfm.installation` | Physical client locations | `client_id`, `address`, `city`, `employee_count`, `installation_type` |
| `wfm.installation.service` | Services at installations | `installation_id`, `service_type`, `required_specialty` |
| `wfm.contract` | Client contracts | `client_id`, `start_date`, `end_date`, `annual_value` |
| `wfm.contract.service` | Services in contracts | `contract_id`, `service_type`, `annual_hours` |
| `wfm.visit` | OHS visit appointments | `client_id`, `installation_id`, `partner_id`, `visit_date`, `state` |
| `wfm.visit.stage` | Kanban stages | `name`, `sequence`, `fold` |
| `wfm.sepe.export` | SEPE export records | `name`, `date_from`, `date_to`, `state`, `file_data` |
| `wfm.workflow` | Autonomous workflows | `name`, `trigger_model`, `trigger_field`, `action_type` |
| `wfm.workflow.log` | Workflow execution logs | `workflow_id`, `record_id`, `status`, `error_message` |

### Visit States

```
draft → assigned → confirmed → in_progress → done
                                          ↘ cancelled
```

### Files

```
wfm_core/
├── models/
│   ├── partner.py           # Client/Partner extensions
│   ├── installation.py      # Installation model
│   ├── installation_service.py
│   ├── contract.py          # Contract model
│   ├── contract_service.py
│   ├── visit.py             # Main visit model
│   ├── visit_stage.py       # Kanban stages
│   ├── sepe_export.py       # SEPE exports
│   ├── workflow.py          # Autonomous workflows
│   └── workflow_log.py      # Execution logs
├── wizard/
│   ├── sepe_export_wizard.py
│   └── sepe_export_wizard_views.xml
├── views/
│   ├── partner_views.xml
│   ├── installation_views.xml
│   ├── contract_views.xml
│   ├── visit_views.xml
│   ├── sepe_export_views.xml
│   ├── billing_dashboard_views.xml
│   ├── workflow_views.xml
│   └── menu.xml
├── data/
│   ├── sequences.xml
│   ├── visit_stages.xml
│   └── workflow_cron.xml
└── security/
    └── ir.model.access.csv
```

---

## wfm_fsm - Field Service Management

**Purpose:** Coordinator tools for managing visits efficiently.

### Models

| Model | Description | Key Fields |
|-------|-------------|------------|
| `wfm.visit` (ext) | Extended for Kanban | `kanban_state`, `color`, dashboard helpers |
| `wfm.partner.client.relationship` | Tracks partner-client history | `partner_id`, `client_id`, `total_visits`, `relationship_score` |
| `wfm.assignment.engine` | Smart assignment algorithm | Scoring methods |
| `wfm.partner.health` | Partner churn risk | `partner_id`, `health_score`, `risk_level`, `decline_rate` |
| `wfm.partner.intervention` | Retention actions | `partner_id`, `intervention_type`, `notes`, `outcome` |
| `wfm.ai.retention.engine` | AI retention strategies | Strategy generation methods |

### Smart Assignment Engine

AI-powered partner recommendations with weighted scoring:

| Factor | Weight | Logic |
|--------|--------|-------|
| Relationship | 35% | Prior visit history with client (TOP PRIORITY) |
| Availability | 25% | No conflicts on visit date |
| Performance | 20% | Completion rate, ratings |
| Proximity | 10% | Same city as installation |
| Workload | 10% | Current assignment balance |

### Churn Analysis

Partner health scoring factors:

| Factor | Description |
|--------|-------------|
| Decline Rate | Ratio of declined visits |
| Volume Change | Month-over-month visit changes |
| Inactivity | Days since last visit |
| Cancellations | Cancellation ratio |
| Rating Trend | Performance rating changes |

Risk levels: `low` (70+), `medium` (50-69), `high` (30-49), `critical` (<30)

### Wizards

| Wizard | Purpose |
|--------|---------|
| `wfm.visit.assign.wizard` | Bulk assign partners to multiple visits |
| `wfm.smart.assign.wizard` | Show recommendations, one-click assign |

### Files

```
wfm_fsm/
├── models/
│   ├── visit_fsm.py           # Visit extensions
│   ├── partner_relationship.py # Relationship tracking
│   ├── assignment_engine.py    # Smart assignment
│   ├── dashboard.py           # Dashboard data
│   ├── partner_health.py      # Churn risk scoring
│   ├── partner_intervention.py # Retention actions
│   └── ai_retention_engine.py # AI strategies
├── views/
│   ├── visit_fsm_views.xml
│   ├── partner_relationship_views.xml
│   ├── churn_dashboard_views.xml
│   ├── dashboard_views.xml
│   └── menu.xml
├── wizard/
│   ├── smart_assign_wizard.py
│   └── smart_assign_wizard_views.xml
└── static/src/
    ├── scss/dashboard.scss
    ├── js/dashboard.js
    └── xml/dashboard.xml
```

---

## wfm_portal - Partner Portal

**Purpose:** Backend interface for OHS partners (limited user access).

### Models

| Model | Description | Key Fields |
|-------|-------------|------------|
| `wfm.partner.availability` | Availability calendar | `partner_id`, `date`, `is_available`, `notes` |

### Features

- Partners see only their assigned visits
- View visit details (client, location, time)
- Accept/confirm visits
- Manage availability calendar
- Update profile information

### Security Groups

| Group | Access |
|-------|--------|
| `group_wfm_partner` | Read own visits, write availability |

### Files

```
wfm_portal/
├── models/
│   └── partner_availability.py
├── views/
│   ├── wfm_portal_views.xml
│   ├── wfm_availability_views.xml
│   ├── wfm_profile_views.xml
│   └── wfm_portal_menus.xml
└── security/
    ├── wfm_portal_security.xml
    └── ir.model.access.csv
```

---

## wfm_whatsapp - WhatsApp Integration

**Purpose:** Autonomous notification agent via Twilio.

### Models

| Model | Description | Key Fields |
|-------|-------------|------------|
| `wfm.whatsapp.message` | Message log | `partner_id`, `message_body`, `status`, `twilio_sid` |
| `wfm.visit` (ext) | Auto-notify on assignment | `_trigger_whatsapp_notification()` |

### Controllers

| Endpoint | Purpose |
|----------|---------|
| `POST /whatsapp/webhook` | Receive incoming messages from Twilio |
| `POST /whatsapp/status` | Delivery status callbacks |

### WhatsApp Commands

| Command | Action |
|---------|--------|
| `ACCEPT` / `YES` | Confirm latest assigned visit |
| `DENY` / `NO` | Decline latest assigned visit |
| `visits` | List upcoming visits |
| `visit 1` | Show details of visit #1 |
| `visit 1 accept` | Confirm specific visit |
| `visit 2 deny` | Decline specific visit |
| `status` | Check current assignment status |
| `help` | Show available commands |

### Files

```
wfm_whatsapp/
├── models/
│   ├── whatsapp_message.py
│   └── visit_whatsapp.py
├── controllers/
│   └── webhook.py
├── views/
│   ├── whatsapp_message_views.xml
│   └── visit_whatsapp_views.xml
├── wizard/
│   ├── whatsapp_compose.py
│   └── whatsapp_compose_views.xml
└── data/
    ├── message_templates.xml
    └── scheduled_actions.xml
```

---

## wfm_ai_chat - AI Chat Integration

**Purpose:** Natural language interface using LLM with WFM-specific tools.

### Models

| Model | Description | Key Fields |
|-------|-------------|------------|
| `wfm.chat.session` | Chat conversation | `user_id`, `messages`, `context` |
| `wfm.llm.client` | LLM API client | Tool execution methods |

### Available Tools

#### Visit Management
| Tool | Description |
|------|-------------|
| `wfm_list_visits` | Query visits with filters |
| `wfm_get_visit` | Single visit details |
| `wfm_create_visit` | Create new visit |
| `wfm_update_visit` | Update visit fields |
| `wfm_assign_partner` | Assign partner to visit |

#### Partner Management
| Tool | Description |
|------|-------------|
| `wfm_list_partners` | Query partners |
| `wfm_partner_availability` | Check availability |
| `wfm_recommendations` | Get assignment suggestions |

#### Churn Analysis
| Tool | Description |
|------|-------------|
| `wfm_list_at_risk_partners` | Partners at risk of churning |
| `wfm_get_partner_health` | Detailed churn risk analysis |
| `wfm_log_retention_action` | Log retention intervention |
| `wfm_resolve_retention_ticket` | Resolve retention ticket |
| `wfm_churn_dashboard_stats` | Dashboard statistics |
| `wfm_get_ai_retention_strategy` | AI-powered retention strategy |
| `wfm_run_churn_computation` | Trigger churn risk computation |

#### Dashboard
| Tool | Description |
|------|-------------|
| `wfm_dashboard_data` | Aggregate statistics |
| `wfm_send_whatsapp` | Send WhatsApp message |

### Files

```
wfm_ai_chat/
├── models/
│   ├── chat_session.py
│   └── llm_client.py
├── tools/
│   └── wfm_tools.py
├── views/
│   └── chat_views.xml
└── data/
    └── system_prompt.xml
```

---

## web_timeline - OCA Module

**Purpose:** Third-party module providing Gantt/Timeline view.

**Source:** [OCA/web](https://github.com/OCA/web)

Used by `wfm_fsm` for partner schedule visualization.

---

## Installation

### Production Deployment

```bash
# SSH to server
ssh gaurav-vm

# Update code
cd /opt/odoo/workforce-management
git pull origin dev-a

# Copy addons
cp -r addons/wfm_core /opt/odoo/addons/
cp -r addons/wfm_fsm /opt/odoo/addons/
cp -r addons/wfm_portal /opt/odoo/addons/
cp -r addons/wfm_whatsapp /opt/odoo/addons/
cp -r addons/wfm_ai_chat /opt/odoo/addons/
cp -r addons/web_timeline /opt/odoo/addons/

# Restart Odoo
docker restart odoo
```

### Module Upgrade

```bash
# In Odoo container
odoo -d deeprunner -u wfm_core,wfm_fsm,wfm_ai_chat --stop-after-init
```

---

## Environment Variables

Required for `wfm_whatsapp`:

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=+14155238886
```

Required for `wfm_ai_chat`:

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Or compatible API endpoint
LLM_API_BASE=https://api.openai.com/v1
```
