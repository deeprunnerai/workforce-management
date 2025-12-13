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

## Documentation Maintenance (IMPORTANT)

**All developers MUST keep documentation up to date.** Update these files after completing tasks:

| File | Purpose | Update When |
|------|---------|-------------|
| `STATUS.md` | Project progress, branch status, KPIs | After each deployment, data change, or milestone |
| `CLAUDE.md` | Technical context, models, roadmap | After adding models, features, or architecture changes |
| `CHANGELOG.md` | Version history | After each merge to main |
| `TASKS.md` | Task tracking | After completing or starting tasks |

### Update Checklist (Run after each work session)
```bash
# 1. Update STATUS.md with current progress
# 2. Update CHANGELOG.md if merging to main
# 3. Commit and push documentation
git add *.md && git commit -m "docs: update project status" && git push

# 4. Sync all branches
for branch in dev-a dev-b dev-c; do
  git checkout $branch && git merge main --no-edit && git push origin $branch
done
git checkout main
```

### Documentation Rules
1. **STATUS.md** - Update module status, data counts, branch commits after EVERY deployment
2. **CLAUDE.md** - Update data models section when adding/modifying models
3. **Keep branches synced** - Always sync dev-a, dev-b, dev-c with main after merging
4. **Timestamp updates** - Add "Last Updated" date at bottom of STATUS.md

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
  ├── Contract (Agreement with client)
  │     └── Contract Service (OHS service type + hours)
  │           └── Installation Service (Partner assigned to installation)
  │                 └── Visit (Scheduled appointment)
  └── Installation (Branch/Location)
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
ssh gaurav-vm "cd /opt/odoo/workforce-management && git pull origin dev-a && cp -r addons/wfm_core /opt/odoo/addons/ && docker restart odoo"
```

### Custom Addons (use `wfm_*` prefix)

| Module | Purpose | Status | Branch |
|--------|---------|--------|--------|
| `wfm_core` | Data models, business logic | ✅ Deployed | main |
| `wfm_fsm` | Field Service Management (Kanban, dashboard) | ✅ Deployed | main |
| `wfm_portal` | Partner self-service portal | 📋 In Progress | dev-a |
| `wfm_whatsapp` | Twilio WhatsApp integration | 📋 Planned | dev-c |

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

### wfm.contract
- `name`, `code` - Contract name and auto-generated code (CON prefix)
- `client_id` - Many2one to client
- `start_date`, `end_date` - Contract period
- `is_indefinite` - Boolean for open-ended contracts
- `contract_value`, `currency_id` - Financial terms
- `characterization` - Selection (main/secondary/amendment)
- `state` - Selection (draft/active/expired/cancelled)
- `service_ids` - One2many to contract services

### wfm.contract.service
- `code` - Auto-generated code (SVC prefix)
- `contract_id` - Many2one to contract
- `client_id` - Related from contract
- `service_type` - Selection (physician/safety_engineer)
- `start_date`, `end_date` - Service period
- `assigned_hours`, `price_per_hour` - Hourly services
- `quantity`, `price_per_unit` - Fixed services
- `state` - Selection (draft/active/completed/cancelled)
- `installation_service_ids` - One2many to installation services

### wfm.installation.service
- `code` - Auto-generated code (ISVC prefix)
- `contract_service_id` - Many2one to contract service
- `installation_id` - Many2one to installation
- `partner_id` - Many2one to assigned partner
- `assigned_hours`, `programmed_hours`, `completed_hours`, `remaining_hours`
- `start_date`, `end_date` - Assignment period
- `state` - Selection (draft/assigned/in_progress/completed/cancelled)
- `visit_ids` - One2many to visits

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

---

## Autonomous Notification Agent

**Trigger:** Visit assigned to Partner (state change)

**Actions:**
1. Send WhatsApp message via Twilio
2. Create in-app notification
3. Log action in audit trail

```python
def write(self, vals):
    result = super().write(vals)
    if 'partner_id' in vals and vals['partner_id']:
        self._send_whatsapp_notification()
        self._send_inapp_notification()
    return result
```

### Notification Triggers

| Event | WhatsApp | In-app | Email |
|-------|----------|--------|-------|
| Partner assigned | Yes | Yes | No |
| Schedule confirmed | Yes | Yes | Yes |
| Change request | Yes | Yes | No |
| 24h reminder | Yes | No | No |

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

### GEP Partner (External)
- Conduct OHS visits, submit reports, get paid
- Self-service portal, instant notifications

---

## File Structure

```
workforce-management/
├── addons/
│   ├── wfm_core/           # Core models
│   │   ├── models/
│   │   ├── views/
│   │   ├── security/
│   │   └── data/
│   ├── wfm_fsm/            # Kanban & dashboard
│   ├── wfm_portal/         # Partner portal
│   └── wfm_whatsapp/       # Twilio integration
├── scripts/
├── docker/
└── README.md
```

---

## Environment Variables

```bash
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
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

## Out of Scope (Phase 1)

- SEPE export automation
- AI assignment suggestions
- Availability calendar
- Visit report submission
- Payment/accounting integration

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

### Phase 3: Reporting & Compliance (Future)
- SEPE export automation
- Billing integration
- Partner payments

---

## Development Roadmap

### dev-a: Partner Portal (wfm_portal)

**Goal:** Self-service portal for external partners to view assignments, confirm visits, and submit reports.

**Features:**
1. **Partner Dashboard**
   - View assigned visits (calendar + list)
   - Upcoming visits summary
   - Hours completed vs assigned

2. **Visit Management**
   - Accept/decline visit assignments
   - Confirm attendance
   - Mark visit as started/completed
   - Submit visit notes

3. **Schedule View**
   - Monthly/weekly calendar
   - Filter by client/installation
   - Export to iCal

4. **Notifications**
   - View notification history
   - Mark as read/unread

**Technical:**
- Extends `portal` module
- Uses `website` for frontend
- Access rules for partner-only data

### dev-c: WhatsApp Integration (wfm_whatsapp)

**Goal:** Automated WhatsApp notifications via Twilio when visits are assigned or updated.

**Features:**
1. Send notification on partner assignment
2. Send 24h reminder before visit
3. Send confirmation request
4. Handle partner responses

**Technical:**
- Twilio WhatsApp Business API
- Webhook for incoming messages
- Message templates for Greek language

---

## Current Data Summary

| Entity | Count |
|--------|-------|
| Clients | 10 |
| Installations | 50 |
| Partners | 100 |
| Contracts | 17 (10 active, 3 draft, 2 expired, 2 cancelled) |
| Contract Services | 20 |
| Installation Services | 100 |
| Visits | 200 |
