# WFM Odoo Modules

Complete list of custom Odoo 19 modules developed for the GEP OHS Workforce Management System.

## Module Overview

| Module | Version | Status | Description |
|--------|---------|--------|-------------|
| `wfm_core` | 19.0.1.0.0 | Production | Core data models, workflows |
| `wfm_fsm` | 19.0.2.0.0 | Production | Kanban, Dashboard, Smart Assignment |
| `wfm_portal` | 19.0.1.0.0 | Production | Partner self-service backend |
| `wfm_whatsapp` | 19.0.1.0.0 | Production | Twilio WhatsApp integration |
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
    │  wfm_fsm   │  │ wfm_portal │  │    ...     │
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
│   └── visit_stage.py       # Kanban stages
├── views/
│   ├── partner_views.xml
│   ├── installation_views.xml
│   ├── installation_service_views.xml
│   ├── contract_views.xml
│   ├── contract_service_views.xml
│   ├── visit_views.xml
│   └── menu.xml
├── data/
│   ├── sequences.xml        # Visit number sequence (VISIT/00001)
│   └── visit_stages.xml     # Default stages
├── demo/
│   └── demo_data.xml        # Sample data
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

### Smart Assignment Engine

AI-powered partner recommendations with weighted scoring:

| Factor | Weight | Logic |
|--------|--------|-------|
| Relationship | 35% | Prior visit history with client (TOP PRIORITY) |
| Availability | 25% | No conflicts on visit date |
| Performance | 20% | Completion rate, ratings |
| Proximity | 10% | Same city as installation |
| Workload | 10% | Current assignment balance |

**Key Methods:**
- `get_recommended_partners(visit_id, limit=2)` - Returns top partners with scores
- `assign_partner_to_visit(visit_id, partner_id)` - Assign and notify

### Wizards

| Wizard | Purpose |
|--------|---------|
| `wfm.visit.assign.wizard` | Bulk assign partners to multiple visits |
| `wfm.smart.assign.wizard` | Show recommendations, one-click assign |

### Dashboard

Custom OWL component showing:
- 4 color-coded cards (Draft, Assigned, In Progress, Completed)
- Click-through to filtered visit list
- Real-time counts

### Files

```
wfm_fsm/
├── models/
│   ├── visit_fsm.py           # Visit extensions
│   ├── partner_relationship.py # Relationship tracking
│   ├── assignment_engine.py    # Smart assignment
│   └── dashboard.py           # Dashboard data
├── views/
│   ├── visit_fsm_views.xml    # Enhanced Kanban
│   ├── gantt_views.xml        # Timeline view
│   ├── partner_relationship_views.xml
│   ├── visit_form_extension.xml  # Recommendations table
│   ├── dashboard_views.xml
│   └── menu.xml
├── wizard/
│   ├── visit_assign_wizard.py
│   ├── visit_assign_wizard_views.xml
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
│   ├── wfm_portal_views.xml      # Partner visit list
│   ├── wfm_availability_views.xml # Availability calendar
│   ├── wfm_profile_views.xml     # Profile management
│   └── wfm_portal_menus.xml      # Partner menu
└── security/
    ├── wfm_portal_security.xml   # Groups and rules
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

Partners can interact via WhatsApp:

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

### Wizards

| Wizard | Purpose |
|--------|---------|
| `wfm.whatsapp.compose` | Send custom WhatsApp message |

### Message Templates

| Template | Trigger |
|----------|---------|
| `visit_assignment` | Partner assigned to visit |
| `visit_reminder_24h` | 24 hours before visit |
| `visit_cancelled` | Visit cancelled |

### Scheduled Actions

| Action | Schedule |
|--------|----------|
| `Send 24h Reminders` | Daily at 9:00 AM |

### Files

```
wfm_whatsapp/
├── models/
│   ├── whatsapp_message.py    # Message log
│   └── visit_whatsapp.py      # Visit notification triggers
├── controllers/
│   └── webhook.py             # Twilio webhook handler
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
cp -r addons/web_timeline /opt/odoo/addons/

# Restart Odoo
docker restart odoo
```

### Module Upgrade

```bash
# In Odoo container
odoo -d deeprunner -u wfm_core,wfm_fsm,wfm_whatsapp --stop-after-init
```

---

## Environment Variables

Required for `wfm_whatsapp`:

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=+14155238886
```
