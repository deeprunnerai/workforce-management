# Dev A Implementation Plan

## Assignment Overview

**Developer:** Gaurav ([@gauravdr](https://github.com/gauravdr)) <gaurav@deeprunner.ai>
**Branch:** `dev-a`
**Time Budget:** 4 hours
**Deliverables:** Core Models + Seed Data

---

## Scope

### In Scope
1. **wfm_core addon** - Core data models and business logic
2. **Data Models:**
   - `wfm.installation` - Client installations/branches
   - `res.partner` extension - Client and Partner flags + fields
   - `wfm.visit` - OHS visit scheduling
   - `wfm.visit.stage` - Kanban stages for visits
3. **Seed Data:** Demo data for testing (10 clients, 50 installations, 100 partners, 200 visits)
4. **Security:** Access control rules
5. **Views:** Basic form/tree views for data entry

### Out of Scope (Other Devs)
- Kanban pipeline UI (@riya-2098)
- Dashboard widgets (@riya-2098)
- Partner portal (@PanosAndr)
- WhatsApp integration (@PanosAndr)

---

## Technical Approach

### 1. Module Structure
```
addons/wfm_core/
├── __manifest__.py      # Module metadata
├── __init__.py          # Python imports
├── models/
│   ├── __init__.py
│   ├── partner.py       # Client + Partner extensions
│   ├── installation.py  # Installation model
│   ├── visit.py         # Visit model
│   └── visit_stage.py   # Visit stages
├── views/
│   ├── partner_views.xml
│   ├── installation_views.xml
│   ├── visit_views.xml
│   └── menu.xml
├── security/
│   └── ir.model.access.csv
├── data/
│   └── visit_stages.xml  # Default stages
└── demo/
    └── demo_data.xml     # Seed data
```

### 2. Model Design

#### res.partner (Extension)
- Add `is_wfm_client` boolean
- Add `is_wfm_partner` boolean
- Add `specialty` selection (for partners)
- Add `hourly_rate` float (for partners)
- Add `installation_ids` One2many relation

#### wfm.installation
- `name` - Char (required)
- `client_id` - Many2one to res.partner (domain: is_wfm_client)
- `address`, `city`, `postal_code` - Location fields
- `employee_count` - Integer
- `installation_type` - Selection

#### wfm.visit.stage
- `name` - Char
- `sequence` - Integer
- `fold` - Boolean

#### wfm.visit
- Relations: `client_id`, `installation_id`, `partner_id`
- Scheduling: `visit_date`, `start_time`, `end_time`
- `stage_id` - Many2one to stages
- `state` - Selection with workflow
- Inherit `mail.thread` for chatter

### 3. Default Visit Stages
1. Draft (seq=10)
2. Assigned (seq=20)
3. Confirmed (seq=30)
4. In Progress (seq=40)
5. Completed (seq=50, fold=True)

### 4. Seed Data Strategy
- Use Greek company names and addresses
- Realistic distribution of installation types
- Partner specialties: 60% physicians, 40% safety engineers
- Visits spread across all stages for demo

---

## Implementation Order

1. **Hour 1:** Module scaffold + Partner model extension
2. **Hour 2:** Installation model + Visit Stage model
3. **Hour 3:** Visit model with full fields
4. **Hour 4:** Seed data + Testing

---

## Dependencies

### Odoo Built-in Modules
- `base` - Core framework
- `contacts` - Partner management
- `mail` - Chatter integration

### External
- None for Dev A scope

---

## Integration Points

### For @riya-2098 (Kanban/Dashboard)
- `wfm.visit` model with `stage_id` for Kanban grouping
- `_read_group_stage_ids` method for stage expansion
- Color computation method `_compute_color`

### For @PanosAndr (Portal/WhatsApp)
- `wfm.visit.write()` hook for notification trigger
- Partner model with `phone` field for WhatsApp

---

## Testing Checklist

- [ ] Admin can create client with installations
- [ ] Admin can create partner with specialty
- [ ] Visit can be created and linked to client/installation
- [ ] Stage changes work correctly
- [ ] Seed data loads without errors
- [ ] Access rights allow CRUD for admin users

---
---

# Dev B Implementation Plan

## Assignment Overview

**Developer:** Riya ([@riya-2098](https://github.com/riya-2098))
**Branch:** `dev-b`
**Deliverables:** Coordinator Dashboard, Kanban Pipeline, Smart Assignment Engine

---

## Scope

### In Scope
1. **wfm_fsm addon** - Field Service Management features
2. **Features:**
   - Coordinator Dashboard with color-coded cards
   - Visit Kanban Pipeline with drag-drop stages
   - Calendar view for visits
   - Smart Partner Assignment Engine (AI-powered recommendations)
   - Partner-Client Relationship tracking
3. **Models:**
   - `wfm.partner.client.relationship` - Relationship history
   - `wfm.assignment.engine` - Scoring algorithm
   - `wfm.smart.assign.wizard` - Assignment wizard UI

### Out of Scope (Other Devs)
- Core data models (@gauravdr - dev-a)
- Partner portal (@PanosAndr)
- WhatsApp integration (@PanosAndr)

---

## Technical Approach

### 1. Module Structure
```
addons/wfm_fsm/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── visit_fsm.py           # Visit extensions (coordinator, overdue, recommendations)
│   ├── partner_relationship.py # Partner-Client relationship tracking
│   └── assignment_engine.py    # AI scoring algorithm
├── wizard/
│   ├── __init__.py
│   ├── visit_assign_wizard.py
│   ├── visit_assign_wizard_views.xml
│   ├── smart_assign_wizard.py
│   └── smart_assign_wizard_views.xml
├── views/
│   ├── visit_fsm_views.xml     # Kanban, Calendar views
│   ├── visit_form_extension.xml # Form extensions
│   ├── partner_relationship_views.xml
│   ├── dashboard_views.xml
│   └── menu.xml
├── security/
│   └── ir.model.access.csv
└── static/src/
    └── js/dashboard.js
```

### 2. Smart Assignment Engine

#### Scoring Algorithm (100 points total)
| Factor | Weight | Max Points | Logic |
|--------|--------|------------|-------|
| Relationship | 35% | 35 | Prior visits to this client |
| Availability | 25% | 25 | No conflicts on visit date |
| Performance | 20% | 20 | Completion rate, ratings |
| Proximity | 10% | 10 | Same city as installation |
| Workload | 10% | 10 | Balanced assignments |

#### Key Methods
- `get_recommended_partners(visit_id, limit=2)` - Returns top N recommendations
- `assign_partner_to_visit(visit_id, partner_id)` - Assigns and updates state
- `_compute_relationship_score()` - Based on visit history
- `_compute_availability_score()` - Check schedule conflicts
- `_compute_performance_score()` - Based on ratings/completion
- `_compute_proximity_score()` - City matching
- `_compute_workload_score()` - Assignment balance

### 3. Dashboard Color Codes
| Color | State | Meaning |
|-------|-------|---------|
| Green | done | Completed visits |
| Yellow | assigned/confirmed | Upcoming visits (future date) |
| Orange | in_progress | Active visits |
| Red | draft/assigned (past date) | Overdue/needs attention |

---

## Implementation Order

### Phase 1: Core FSM Features ✅
1. Visit Kanban pipeline with stage grouping
2. Drag-drop stage transitions
3. State/stage synchronization
4. Calendar view

### Phase 2: Coordinator Dashboard ✅
1. Color-coded summary cards
2. Click-through to filtered lists
3. Today's visits quick view

### Phase 3: Smart Assignment Engine ✅
1. Partner-Client relationship model
2. Assignment engine with scoring
3. Smart Assign wizard
4. Form view recommendations

---

## Dependencies

### From wfm_core (Dev A)
- `wfm.visit` model
- `wfm.visit.stage` model
- `res.partner` with `is_wfm_partner`, `is_wfm_client`
- `wfm.installation` model

### Odoo Built-in
- `web` - Dashboard client action
- `mail` - Activity tracking

---

## Integration Points (Dev B)

### For @PanosAndr (Portal/WhatsApp)
- Assignment triggers notification via `action_assign()` method
- Relationship data available for partner portal display

---

## Files Created (Dev B)

| File | Purpose |
|------|---------|
| `models/visit_fsm.py` | Visit extensions with recommendations |
| `models/partner_relationship.py` | Relationship tracking model |
| `models/assignment_engine.py` | AI scoring algorithm |
| `wizard/smart_assign_wizard.py` | Assignment wizard logic |
| `wizard/smart_assign_wizard_views.xml` | Wizard form view |
| `views/visit_form_extension.xml` | Smart Assign button + recommendations |
| `views/partner_relationship_views.xml` | Relationship list/form views |
| `views/visit_fsm_views.xml` | Kanban, calendar, list views |
| `views/dashboard_views.xml` | Dashboard client action |
| `views/menu.xml` | Coordinator menu items |
