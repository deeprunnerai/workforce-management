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
