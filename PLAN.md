# WFM Implementation Plan

**Last Updated:** 2025-12-13

---

## Project Overview

GEP OHS Workforce Management System - Odoo 19 implementation for managing occupational health & safety visits with 100+ external partners serving 3,500+ organizations.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Odoo 19 Community                        │
├─────────────────────────────────────────────────────────────┤
│  wfm_core          │  wfm_fsm           │  wfm_portal       │
│  - Visit model     │  - Dashboard       │  - Partner views  │
│  - Client model    │  - Kanban          │  - Availability   │
│  - Partner model   │  - Smart Assign    │  - My Profile     │
│  - Contract model  │  - Timeline        │  - Visit actions  │
├─────────────────────────────────────────────────────────────┤
│  wfm_whatsapp (planned)                                     │
│  - Twilio integration                                       │
│  - Notification templates                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Completed Phases

### Phase 1: Core Data Models (wfm_core)
- Visit workflow with states (Draft → Assigned → Confirmed → In Progress → Done)
- Client and Installation management
- Partner management with specialties
- Contract and service tracking

### Phase 2: Coordinator Tools (wfm_fsm)
- Kanban pipeline with drag-drop assignment
- Coordinator dashboard with stats
- Calendar and Timeline views
- Smart Assignment Engine with AI scoring
- Partner-Client relationship tracking

### Phase 3: Partner Portal (wfm_portal)
- Backend portal for partners
- Visit views (list, kanban, calendar, form)
- Availability calendar
- My Profile management
- Visit lifecycle actions

### Phase 4: Menu Reorganization
- Flat dropdown navigation
- Filtered views (Physicians, Engineers)
- Timeline views per section

---

## Remaining Phases

### Phase 5: WhatsApp Notifications (wfm_whatsapp)
**Priority:** High

Create autonomous notification agent using Twilio:
- Assignment notification to partner
- Confirmation notification
- 24-hour reminder
- Message logging

### Phase 6: Visit Reports
**Priority:** Medium

Enable partners to submit visit reports:
- Report model with attachments
- Auto-complete workflow
- Admin review capability

### Phase 7: Payment Reports
**Priority:** Medium

Partner payment visibility:
- Excel export of completed visits
- Date range filtering
- Earnings summary

### Phase 8: SEPE Integration
**Priority:** Low

Compliance reporting:
- Export format per Greek regulations
- Automated submission queue

---

## User Roles

| Role | Access | Key Features |
|------|--------|--------------|
| GEP Admin | Full | All modules, configuration |
| GEP Coordinator | Operations | Dashboard, Smart Assign, Visit management |
| GEP Partner | Portal | Own visits, availability, profile |

---

## Production Environment

| Component | Details |
|-----------|---------|
| URL | https://odoo.deeprunner.ai |
| Server | gaurav-vm (Docker) |
| Database | PostgreSQL |
| Modules | wfm_core, wfm_fsm, wfm_portal |

---

## Integration Points

### WhatsApp (Twilio)
```python
# Trigger point in wfm.visit
def _trigger_notification_agent(self):
    # Override in wfm_whatsapp to send messages
    pass
```

### SEPE Export (Future)
```python
# Export hook in wfm.visit
def action_export_sepe(self):
    # Generate compliance report
    pass
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Twilio API limits | Implement rate limiting, message queue |
| Partner adoption | Simple UX, training materials |
| Data quality | Validation rules, seed data review |

---

## Success Metrics

- [ ] 100% partner accounts created
- [ ] WhatsApp delivery rate > 95%
- [ ] Visit completion rate tracked
- [ ] Partner satisfaction > 4/5
