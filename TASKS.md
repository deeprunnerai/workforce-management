# Dev A Tasks

**Developer:** Gaurav ([@gauravdr](https://github.com/gauravdr)) <gaurav@deeprunner.ai>
**Branch:** `dev-a`

---

## Task Breakdown

### Phase 1: Module Scaffold (30 min)

- [ ] **T1.1** Create `__manifest__.py` with module metadata
- [ ] **T1.2** Create `__init__.py` files for package structure
- [ ] **T1.3** Create empty model files
- [ ] **T1.4** Create `ir.model.access.csv` security file

### Phase 2: Partner Extension (45 min)

- [ ] **T2.1** Add `is_wfm_client` boolean field to res.partner
- [ ] **T2.2** Add `is_wfm_partner` boolean field to res.partner
- [ ] **T2.3** Add `specialty` selection field (physician/safety_engineer/health_scientist)
- [ ] **T2.4** Add `hourly_rate` float field
- [ ] **T2.5** Create partner form view extension for WFM fields
- [ ] **T2.6** Create tree views for clients and partners

### Phase 3: Installation Model (45 min)

- [ ] **T3.1** Create `wfm.installation` model with fields:
  - `name` (required)
  - `client_id` (Many2one)
  - `address`, `city`, `postal_code`
  - `employee_count`
  - `installation_type` (selection)
- [ ] **T3.2** Add `installation_ids` One2many to res.partner
- [ ] **T3.3** Create installation form view
- [ ] **T3.4** Create installation tree view
- [ ] **T3.5** Add installation action and menu item

### Phase 4: Visit Stage Model (15 min)

- [ ] **T4.1** Create `wfm.visit.stage` model:
  - `name`
  - `sequence`
  - `fold`
- [ ] **T4.2** Create default stages data file (5 stages)

### Phase 5: Visit Model (60 min)

- [ ] **T5.1** Create `wfm.visit` model base fields:
  - `name` (auto-generated reference)
  - `client_id`, `installation_id`, `partner_id`
  - `visit_date`, `start_time`, `end_time`
  - `duration` (computed)
- [ ] **T5.2** Add `stage_id` and `state` fields
- [ ] **T5.3** Inherit `mail.thread` and `mail.activity.mixin`
- [ ] **T5.4** Implement `_read_group_stage_ids` for Kanban expansion
- [ ] **T5.5** Implement `_compute_color` for dashboard colors
- [ ] **T5.6** Add `write()` override hook for notification trigger
- [ ] **T5.7** Create visit form view
- [ ] **T5.8** Create visit tree view
- [ ] **T5.9** Add visit action and menu item

### Phase 6: Menu Structure (15 min)

- [ ] **T6.1** Create root menu "Workforce Management"
- [ ] **T6.2** Create submenu structure:
  - Operations > Visits
  - Configuration > Clients
  - Configuration > Installations
  - Configuration > Partners
  - Configuration > Visit Stages

### Phase 7: Seed Data (30 min)

- [ ] **T7.1** Create 10 Greek client companies
- [ ] **T7.2** Create 50 installations (5 per client)
- [ ] **T7.3** Create 100 partners (60 physicians, 40 engineers)
- [ ] **T7.4** Create 3 coordinator users
- [ ] **T7.5** Create 200 visits across all stages

### Phase 8: Testing & Validation (20 min)

- [ ] **T8.1** Install module on Odoo
- [ ] **T8.2** Verify all models are accessible
- [ ] **T8.3** Test CRUD operations on each model
- [ ] **T8.4** Verify seed data loaded correctly
- [ ] **T8.5** Test stage transitions on visits
- [ ] **T8.6** Verify integration points work for Dev B/C

---

## Task Dependencies

```
T1.x (Scaffold) → T2.x (Partner) → T3.x (Installation)
                                 ↘
                                   T4.x (Stage) → T5.x (Visit) → T6.x (Menu)
                                                               ↘
                                                                 T7.x (Seed) → T8.x (Test)
```

---

## Acceptance Criteria

### Module Installation
- [ ] Module appears in Odoo Apps list
- [ ] Module installs without errors
- [ ] All dependencies resolved

### Data Models
- [ ] All 4 models created and accessible
- [ ] Fields match specification
- [ ] Relations work correctly

### Views
- [ ] Form views allow data entry
- [ ] Tree views display records
- [ ] Menu navigation works

### Seed Data
- [ ] 10 clients created
- [ ] 50 installations linked to clients
- [ ] 100 partners with specialties
- [ ] 200 visits in various stages

### Integration
- [ ] Visit model has hooks for @PanosAndr notifications
- [ ] Stage grouping works for @riya-2098 Kanban

---
---

# Dev B Tasks

**Developer:** Riya ([@riya-2098](https://github.com/riya-2098))
**Branch:** `dev-b`

---

## Task Breakdown

### Phase 1: wfm_fsm Module Setup ✅

- [x] **T1.1** Create `__manifest__.py` with wfm_core dependency
- [x] **T1.2** Create `__init__.py` files for package structure
- [x] **T1.3** Create `ir.model.access.csv` security file

### Phase 2: Kanban Pipeline ✅

- [x] **T2.1** Create visit Kanban view with stage grouping
- [x] **T2.2** Implement drag-drop stage transitions
- [x] **T2.3** Add state/stage synchronization in `write()` override
- [x] **T2.4** Create pipeline action with proper defaults
- [x] **T2.5** Add kanban card styling (colors, icons)

### Phase 3: Coordinator Dashboard ✅

- [x] **T3.1** Create dashboard client action
- [x] **T3.2** Implement `get_dashboard_data()` method
- [x] **T3.3** Add color-coded summary cards (green/yellow/orange/red)
- [x] **T3.4** Implement `get_visits_action()` for filtered views
- [x] **T3.5** Create dashboard JavaScript component

### Phase 4: Calendar View ✅

- [x] **T4.1** Create visit calendar view
- [x] **T4.2** Add calendar action and menu item

### Phase 5: Smart Assignment Engine ✅

- [x] **T5.1** Create `wfm.partner.client.relationship` model:
  - `partner_id`, `client_id` (Many2one)
  - `total_visits`, `completed_visits`
  - `avg_rating`, `on_time_rate`
  - `relationship_score` (computed)
  - `first_visit_date`, `last_visit_date`
- [x] **T5.2** Create `wfm.assignment.engine` model with scoring:
  - `get_recommended_partners(visit_id, limit=2)`
  - `assign_partner_to_visit(visit_id, partner_id)`
  - Relationship score (35%)
  - Availability score (25%)
  - Performance score (20%)
  - Proximity score (10%)
  - Workload score (10%)
- [x] **T5.3** Create `wfm.smart.assign.wizard`:
  - Top 2 recommendations display
  - One-click assign buttons
  - Manual selection option
  - AI reasoning explanation

### Phase 6: Visit Form Extensions ✅

- [x] **T6.1** Add `coordinator_id` field to visit
- [x] **T6.2** Add `recommendation_html` computed field
- [x] **T6.3** Add Smart Assign button (visible when no partner)
- [x] **T6.4** Add recommendation table to form view
- [x] **T6.5** Hide Smart Assign when partner already assigned
- [x] **T6.6** Add contextual alerts for AI reasoning

### Phase 7: Menu Structure ✅

- [x] **T7.1** Create Coordinator submenu
- [x] **T7.2** Add menu items:
  - Dashboard
  - Pipeline
  - Today
  - Calendar
  - Unassigned
  - Overdue
- [x] **T7.3** Add Partner Relationships under Configuration

### Phase 8: Testing & Validation ✅

- [x] **T8.1** Module installs without errors
- [x] **T8.2** Kanban drag-drop works correctly
- [x] **T8.3** Dashboard shows correct counts
- [x] **T8.4** Smart Assign recommendations appear
- [x] **T8.5** Wizard assigns partner correctly
- [x] **T8.6** State/stage sync works on assignment

---

## Acceptance Criteria (Dev B)

### Module Installation
- [x] wfm_fsm module appears in Apps list
- [x] Module installs without errors
- [x] Depends on wfm_core correctly

### Kanban Pipeline
- [x] Visits grouped by stage
- [x] Drag-drop changes state
- [x] Colors reflect status

### Dashboard
- [x] Color-coded cards display counts
- [x] Click opens filtered list

### Smart Assignment
- [x] Top 2 recommendations shown
- [x] Scores explained with AI reasoning
- [x] One-click assign works
- [x] Relationship updated on completion
