# GEP OHS Workforce Management System - Claude Context

## Project Overview

**GEP Group** (gepgroup.gr) is Greece's largest Occupational Health & Safety (OHS) service provider. This system manages their B2B consulting operations with 100+ external partners (physicians, safety engineers) serving 3,500+ organizations across 13K facilities.

### Business Model
- **B2B OHS Consulting** - ~€17.6M revenue, 160 employees
- **Workforce Network Model** - 100+ external partners (contractors)
- **Compliance-Driven** - Greek law mandates OHS services

### Financial Flow
```
Client pays GEP → GEP pays Partner → GEP keeps margin
```

---

## Key Terminology

| Term | Greek | Definition |
|------|-------|------------|
| **Client** | Πελάτης | Business purchasing OHS services |
| **Installation** | Εγκατάσταση | Physical location/branch requiring OHS visits |
| **Partner/Resource** | Συνεργάτης | External OHS professional (physician, safety engineer) |
| **Visit** | Επίσκεψη | Scheduled OHS service delivery |
| **SEPE** | ΣΕΠΕ | Greek Labor Inspectorate (government regulator) |
| **Coordinator** | Συντονιστής | GEP staff managing partner schedules |

### Data Hierarchy
```
Client (Company)
  └── Installation (Branch/Location)
        └── Contract Service (OHS service type)
              └── Visit (Scheduled appointment)
```

---

## Technical Stack

| Component | Details |
|-----------|---------|
| **Platform** | Odoo 19 Community Edition |
| **Production URL** | https://odoo.deeprunner.ai |
| **Server** | gaurav-vm |
| **Local Dev** | Docker Compose |

---

## Odoo 19 Compatibility (IMPORTANT)

**ALWAYS use Odoo 19 syntax.** Key differences from older versions:

### View Syntax Changes

| Old (Odoo 17/18) | New (Odoo 19) |
|------------------|---------------|
| `<tree>` | `<list>` |
| `</tree>` | `</list>` |
| `view_mode="tree,form"` | `view_mode="list,form"` |
| `attrs="{'invisible': [...]}"` | `invisible="condition"` |
| `attrs="{'readonly': [...]}"` | `readonly="condition"` |
| `attrs="{'required': [...]}"` | `required="condition"` |
| `states="draft,confirmed"` | `invisible="state not in ('draft', 'confirmed')"` |

### Python API Changes

| Old | New (Odoo 19) |
|-----|---------------|
| `@api.model` on `_read_group_*` | No decorator needed |
| `_read_group_stage_ids(self, stages, domain, order)` | `_read_group_stage_ids(self, stages, domain)` |
| `context.get('active_id')` in XML | Use `id` field directly |
| `uid` in XML domains | Not available - use different approach |

### View Rules
- Use `<list>` instead of `<tree>` for list/tree views
- Use `invisible="expression"` directly on elements
- Avoid complex Python expressions in XML domains
- Load XML files in dependency order (actions before views that reference them)
- Button context: use `id` not `active_id`

### Deployment
```bash
# Deploy to production
ssh gaurav-vm "cd /opt/odoo/workforce-management && git pull origin dev-a && cp -r addons/* /opt/odoo/addons/ && docker restart odoo"
```

### Custom Addons (use `wfm_*` prefix)

| Module | Purpose | Status |
|--------|---------|--------|
| `wfm_core` | Data models, SEPE, billing, workflows | ✅ Deployed |
| `wfm_fsm` | Dashboard, Smart Assignment, Churn Analysis | ✅ Deployed |
| `wfm_portal` | Partner self-service portal | ✅ Deployed |
| `wfm_whatsapp` | Twilio WhatsApp integration | ✅ Deployed |
| `wfm_ai_chat` | AI Chat with LLM tools | ✅ Deployed |

---

## Data Models

### wfm.client (extends res.partner)
- `is_wfm_client` - Boolean flag
- `installation_ids` - One2many to installations
- `contract_ids` - One2many to contracts

### wfm.installation
- `name` - Installation name
- `client_id` - Many2one to client
- `address`, `city`, `postal_code`
- `employee_count` - Integer
- `installation_type` - Selection (office/warehouse/factory/retail/construction)

### wfm.partner (extends res.partner)
- `is_wfm_partner` - Boolean flag
- `specialty` - Selection (physician/safety_engineer/health_scientist)
- `hourly_rate` - Float (EUR)
- `city` - For proximity matching

### wfm.visit
- `client_id`, `installation_id`, `partner_id` - Relations
- `visit_date`, `start_time`, `end_time`, `duration`
- `stage_id` - Many2one to visit stages
- `state` - Selection (draft/assigned/confirmed/in_progress/done/cancelled)
- Inherits `mail.thread`, `mail.activity.mixin`

### Visit Stages (wfm.visit.stage)
1. Draft (sequence=10)
2. Assigned (sequence=20)
3. Confirmed (sequence=30)
4. In Progress (sequence=40)
5. Completed (sequence=50)

### wfm.partner.client.relationship (wfm_fsm)
- `partner_id` - Many2one to partner
- `client_id` - Many2one to client
- `total_visits`, `completed_visits` - Visit statistics
- `avg_rating`, `on_time_rate` - Performance metrics
- `relationship_score` - Computed (0-100) based on history
- `first_visit_date`, `last_visit_date` - Timeline

### wfm.partner.health (wfm_fsm)
- `partner_id` - Many2one to partner
- `health_score` - Float (0-100)
- `risk_level` - Selection (low/medium/high/critical)
- `decline_rate`, `volume_change`, `inactivity_days` - Risk factors
- `ticket_state` - Selection (open/in_progress/resolved/closed)

### wfm.workflow (wfm_core)
- `name` - Workflow name
- `trigger_model` - Model to watch
- `trigger_field` - Field to monitor
- `trigger_value` - Value that triggers
- `action_type` - Selection (whatsapp/update_field/webhook)
- `is_active` - Boolean

### wfm.sepe.export (wfm_core)
- `name` - Export name
- `date_from`, `date_to` - Date range
- `state` - Selection (draft/done)
- `file_data` - Binary export file

---

## Smart Partner Assignment (wfm_fsm)

**Purpose:** AI-powered partner recommendations prioritizing relationship continuity.

### Scoring Weights
| Factor | Weight | Logic |
|--------|--------|-------|
| Relationship | 35% | Prior visit history with client (TOP PRIORITY) |
| Availability | 25% | Schedule conflicts on visit date |
| Performance | 20% | Completion rate, ratings |
| Proximity | 10% | Same city as installation |
| Workload | 10% | Current assignment balance |

### Usage Flow
1. Coordinator opens draft visit (no partner assigned)
2. Recommendation table shows Top 2 partners with AI reasoning
3. Click "Smart Assign" button to open wizard
4. Wizard shows detailed score breakdown
5. One-click assign from recommendations or manual selection

---

## Churn Analysis (wfm_fsm)

**Purpose:** Identify partners at risk of leaving and enable proactive retention.

### Health Scoring Factors
| Factor | Weight | Description |
|--------|--------|-------------|
| Decline Rate | 25% | Ratio of declined visits |
| Volume Change | 25% | Month-over-month visit changes |
| Inactivity | 20% | Days since last visit |
| Cancellations | 15% | Cancellation ratio |
| Rating Trend | 15% | Performance rating changes |

### Risk Levels
- **Low** (70-100): Healthy engagement
- **Medium** (50-69): Monitor closely
- **High** (30-49): Intervention needed
- **Critical** (<30): Immediate action required

### AI Chat Tools for Churn
```
wfm_list_at_risk_partners    - Query at-risk partners
wfm_get_partner_health       - Detailed health analysis
wfm_log_retention_action     - Log intervention
wfm_resolve_retention_ticket - Close retention case
wfm_churn_dashboard_stats    - Dashboard statistics
wfm_get_ai_retention_strategy - AI recommendations
wfm_run_churn_computation    - Trigger health calculation
```

---

## Autonomous Notification Agent

**Trigger:** Visit assigned to Partner (state change)

**Actions:**
1. Send WhatsApp message via Twilio
2. Create in-app notification
3. Log action in audit trail

### Notification Triggers

| Event | WhatsApp | In-app | Email |
|-------|----------|--------|-------|
| Partner assigned | Yes | Yes | No |
| Schedule confirmed | Yes | Yes | Yes |
| Change request | Yes | Yes | No |
| 24h reminder | Yes | No | No |

---

## Autonomous Workflow Engine (wfm_core)

**Purpose:** Trigger-based automation for business processes.

### Workflow Types
| Action Type | Description |
|-------------|-------------|
| `whatsapp` | Send WhatsApp message |
| `update_field` | Update record field |
| `webhook` | POST to external URL |

### Usage
1. Create workflow with trigger conditions
2. System monitors specified model/field
3. When trigger fires, action executes
4. Execution logged for audit

---

## Dashboard Color Codes

| Color | State | Meaning |
|-------|-------|---------|
| Green | Completed | Work done |
| Yellow | Assigned | Task assigned, future date |
| Orange | In Progress | Partner has started |
| Red | Action Required | Delayed, needs attention |

---

## User Roles

### GEP Admin
- Manage clients, contracts, SEPE reports, billing
- Single source of truth, compliance automation

### GEP Coordinator
- Assign partners to visits, handle change requests
- Drag-drop assignment, async communication
- Churn analysis and retention actions

### GEP Partner (External)
- Conduct OHS visits, submit reports, get paid
- Self-service portal, instant notifications

---

## Menu Structure

```
Workforce Management
├── Dashboard
├── Visits
│   ├── Kanban
│   ├── Calendar
│   ├── Timeline
│   └── By Client
├── Partners
│   ├── All
│   ├── Physicians
│   └── Engineers
├── Clients
│   ├── All
│   ├── Installations
│   ├── Contracts
│   └── Contract Services
├── Reporting
│   └── SEPE
│       ├── Create Export
│       └── Export History
├── Billing
│   ├── Overview
│   ├── Not Billed
│   ├── Invoiced
│   ├── Client Paid
│   └── Settled
├── Analysis
│   ├── Partner Retention
│   └── Churn Analytics
├── Automation
│   ├── Workflows
│   └── Execution Logs
└── Config
    └── Stages
```

---

## File Structure

```
workforce-management/
├── addons/
│   ├── wfm_core/           # Core models, SEPE, billing, workflows
│   │   ├── models/
│   │   ├── views/
│   │   ├── wizard/
│   │   ├── security/
│   │   └── data/
│   ├── wfm_fsm/            # Dashboard, assignment, churn
│   ├── wfm_portal/         # Partner portal
│   ├── wfm_whatsapp/       # Twilio integration
│   ├── wfm_ai_chat/        # AI Chat with LLM tools
│   └── web_timeline/       # OCA timeline view
├── docker/
├── docs/
└── README.md
```

---

## Environment Variables

```bash
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
OPENAI_API_KEY=xxx
LLM_API_BASE=https://api.openai.com/v1
```

---

## Development Commands

### Odoo Shell
```python
# Create a visit
visit = env['wfm.visit'].create({
    'client_id': 1,
    'installation_id': 1,
    'visit_date': '2025-01-15',
})

# Assign partner (triggers notification agent)
visit.write({'partner_id': 5})

# Get dashboard counts
env['wfm.visit']._get_dashboard_data()

# Check partner health
health = env['wfm.partner.health'].search([('partner_id', '=', 5)])
health.health_score, health.risk_level
```

### MCP Commands
```bash
# List visits
mcp odoo search wfm.visit

# Create client
mcp odoo create res.partner '{"name": "Test Client", "is_wfm_client": true}'

# Update visit
mcp odoo write wfm.visit 1 '{"partner_id": 5}'
```

---

## Seed Data Requirements

| Entity | Count |
|--------|-------|
| Clients | 10 |
| Installations | 50 (5 per client) |
| Partners | 100 |
| Coordinators | 3 |
| Visits | 200 |

Use Greek test data (company names, addresses, partner names).

---

## Workflow Phases

### Phase 1: Contract & Setup
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│      1      │    │      2      │    │      3      │    │      4      │
│   Client    │ -> │  GEP Admin  │ -> │  GEP Admin  │ -> │   System    │
│   signs     │    │   stores    │    │  calculates │    │    syncs    │
│  contract   │    │   data in   │    │   hours per │    │  Softone →  │
│             │    │  Softone    │    │    SEPE     │    │   ERPx10    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
    CLIENT           Softone ERP        SEPE Rules         AUTO SYNC
```

### Phase 2: Visit Assignment & Execution
1. Coordinator assigns partner to visit
2. **Agent** sends WhatsApp notification automatically
3. Partner accepts/confirms schedule
4. Partner conducts visit & submits report
5. Admin submits to SEPE & triggers billing

### Phase 3: Reporting & Compliance
- SEPE export automation ✅
- Billing dashboard ✅
- Partner payments (future)
