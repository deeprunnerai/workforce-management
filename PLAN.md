# Dev C Implementation Plan

## Assignment Overview

**Developer:** Panos ([@PanosAndr](https://github.com/PanosAndr)) <p.andrikopoulos@deeprunner.ai>
**Branch:** `dev-c`
**Time Budget:** 20 hours
**Deliverables:** Partner Backend Portal & WhatsApp Integration

---

## Scope

### In Scope
1. **wfm_portal addon** - Backend interface for OHS partners
2. **Features:**
   - Partner visits view (list, kanban, calendar, form)
   - Partner availability calendar
   - My Profile (contact info, hourly rate)
   - Visit actions (confirm, start, complete, cancel)
   - Visit report submission
   - Payment Excel download
3. **wfm_whatsapp addon** - Twilio WhatsApp integration
4. **Security:** WFM Partner group with restricted access

### Out of Scope (Other Devs)
- Core data models (@gauravdr - Dev A)
- Kanban pipeline UI & Dashboard (@riya-2098 - Dev B)

---

## Technical Approach

### Design Decision: Backend Module vs Website Portal

**Original Plan:** Website portal using `portal` module
**Final Implementation:** Backend module with restricted user group

**Rationale:**
- Simpler implementation using standard Odoo views
- Better UX with full Odoo interface features
- Easier security model with record rules
- No separate template development needed
- Partners get familiar Odoo experience

### Module Structure
```
addons/wfm_portal/
├── __manifest__.py          # Module metadata
├── __init__.py              # Python imports
├── models/
│   ├── __init__.py
│   └── partner_availability.py  # Availability + profile methods
├── views/
│   ├── wfm_portal_views.xml      # Visit views for partners
│   ├── wfm_availability_views.xml # Availability calendar
│   ├── wfm_profile_views.xml     # My Profile form
│   └── wfm_portal_menus.xml      # Partner menu structure
├── security/
│   ├── wfm_portal_security.xml   # Security group + rules
│   └── ir.model.access.csv       # Model access rights
└── wizard/
    └── payment_report_wizard.py  # (Planned) Excel export
```

---

## Implementation Phases

### Phase 1: Partner Backend Portal (COMPLETE)

**Approach Changed:** Converted from website portal to backend Odoo module

1. Created `wfm_portal` module scaffold
2. Created security group `group_wfm_partner` (WFM Partner)
3. Created record rules:
   - Partners see only visits assigned to them
   - Partners can write to their own partner record
4. Created views:
   - List view with status decorations
   - Form view with action buttons
   - Kanban view grouped by state
   - Calendar view
   - Search view with filters
5. Created menu structure under "OHS Partner Portal"
6. Created partner user accounts (6 created, 94 remaining)

---

### Phase 2: Availability Calendar (COMPLETE)

1. Created `wfm.partner.availability` model
   - Fields: `partner_id`, `date_from`, `date_to`, `reason`, `state`
2. Created calendar view for availability
3. Created form view for adding unavailable periods
4. Added menu item "My Availability"
5. Security rules for partners to manage own availability

---

### Phase 2.5: My Profile Feature (COMPLETE)

1. Created profile form view (limited editable fields)
   - Contact info: email, phone
   - Address fields
   - Professional info: specialty (readonly), hourly rate (editable), VAT
2. Created server action `action_open_my_profile`
3. Added security rule for partners to write own partner record
4. Added "My Profile" menu item

---

### Phase 2.6: Visit Actions (COMPLETE)

Partners can manage visit lifecycle:
- **Confirm Visit** - Accept assigned visit
- **Start Visit** - Mark visit as in progress
- **Complete Visit** - Mark visit as done
- **Cancel Visit** - Cancel with confirmation dialog

---

### Phase 3: WhatsApp Integration (NOT STARTED)

- [ ] Create `wfm_whatsapp` module scaffold
- [ ] Create Twilio service (`services/twilio_service.py`)
- [ ] Create WhatsApp message log model
- [ ] Override `_trigger_notification_agent()` from wfm_core
- [ ] Add notification templates (assignment, confirmation, reminder)
- [ ] Test with Twilio sandbox

---

### Phase 4: Visit Report Submission (NOT STARTED)

- [ ] Create `wfm.visit.report` model
- [ ] Add report form to visit detail view
- [ ] File upload capability for attachments
- [ ] Auto-transition to completed state on submission

---

### Phase 5: Partner Payment Excel (NOT STARTED)

- [ ] Create payment report wizard
- [ ] Excel export with visit details and earnings
- [ ] Date range filter
- [ ] Add to partner menu

---

## Security Model

### WFM Partner Group (ID: 85)
- Category: WFM Portal
- Users: Partners with portal access
- Implied: None (standalone group)

### Record Rules
| Rule | Model | Access | Domain |
|------|-------|--------|--------|
| See own visits | wfm.visit | Read | `partner_id = user.partner_id` |
| Manage own visits | wfm.visit | Write | `partner_id = user.partner_id` |
| Manage own availability | wfm.partner.availability | Full | `partner_id = user.partner_id` |
| Edit own profile | res.partner | Write | `id = user.partner_id` |

### Model Access
- `wfm.visit` - Read, Write
- `wfm.installation` - Read
- `res.partner` - Read, Write (own record only via rule)
- `wfm.partner.availability` - Full CRUD

---

## Partner Account Setup

### Creating Partner Accounts
1. Create `res.users` record linked to existing partner
2. Set login (email) and password
3. Add to `group_wfm_partner` (ID: 85)

### Current Status
- Total WFM partners: 100
- With user accounts: 6
- Remaining to create: 94

### Test Credentials
| User | Password | Partner |
|------|----------|---------|
| s.anastasiadis@ohs.gr | partner123 | Δρ. Στέφανος Αναστασιάδης |
| (new accounts) | Partner2025! | Various |

---

## Integration Points

### From wfm_core
- `wfm.visit` model with state workflow
- `_trigger_notification_agent()` hook for WhatsApp
- Partner `phone` field for notifications

### For WhatsApp Module
- Override notification trigger method
- Access partner phone from visit
- Log messages in custom model

---

## Dependencies

### Odoo Built-in Modules
- `base` - Core framework

### Custom Modules
- `wfm_core` - Core models (required)

### External Libraries (for Phase 3)
- `twilio` - WhatsApp API

---

## Files Created

| File | Purpose | Status |
|------|---------|--------|
| `__manifest__.py` | Module metadata | Done |
| `__init__.py` | Package imports | Done |
| `models/partner_availability.py` | Availability model + profile action | Done |
| `views/wfm_portal_views.xml` | Visit views for partners | Done |
| `views/wfm_availability_views.xml` | Availability calendar | Done |
| `views/wfm_profile_views.xml` | My Profile form | Done |
| `views/wfm_portal_menus.xml` | Menu structure | Done |
| `security/wfm_portal_security.xml` | Group + record rules | Done |
| `security/ir.model.access.csv` | Model access rights | Done |

---

**Last Updated:** 2025-12-13
