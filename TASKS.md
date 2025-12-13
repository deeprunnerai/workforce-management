# Dev C Tasks

**Developer:** Panos ([@PanosAndr](https://github.com/PanosAndr)) <p.andrikopoulos@deeprunner.ai>
**Branch:** `dev-c`
**Scope:** Partner Portal & WhatsApp Integration

---

## Task Breakdown (20 hours total)

### Phase 1: Partner Backend Portal (Hours 1-4) - COMPLETE

> **Design Change:** Converted from website portal to backend Odoo module for simpler implementation and better UX.

- [x] **T1.1** Create `wfm_portal` module scaffold:
  - `__manifest__.py` with dependencies (`wfm_core`)
  - `__init__.py` files
  - `models/` directory
  - `views/` directory
  - `security/` directory
- [x] **T1.2** Create security group and record rules:
  - `group_wfm_partner` security group (ID: 85)
  - Record rule: partners see only their assigned visits
  - Record rule: partners can write their own partner record
- [x] **T1.3** Create partner visit views:
  - List view with status decorations
  - Form view with action buttons
  - Kanban view grouped by state
  - Calendar view
  - Search view with filters
- [x] **T1.4** Add model access rights:
  - `wfm.visit` - read, write
  - `wfm.installation` - read
  - `res.partner` - read, write (own record via rule)
- [x] **T1.5** Create menu structure under "OHS Partner Portal"
- [x] **T1.6** Create partner user accounts (6 created)

**Deliverable:** Backend interface where partners see their assignments

---

### Phase 2: Availability Calendar (Hours 5-8) - COMPLETE

- [x] **T2.1** Create availability model (`models/partner_availability.py`):
  - `wfm.partner.availability` model
  - Fields: `partner_id`, `date_from`, `date_to`, `reason`, `state`
  - Link to `res.partner` with One2many
- [x] **T2.2** Create availability calendar view (`views/wfm_availability_views.xml`):
  - Calendar widget for viewing availability
  - Form view for adding unavailable periods
- [x] **T2.3** Add menu item "My Availability"
- [x] **T2.4** Security rules for partners to manage own availability
- [x] **T2.5** Test availability workflow

**Deliverable:** Partners can mark dates they're unavailable

---

### Phase 2.5: My Profile Feature (ADDED) - COMPLETE

- [x] **T2.5.1** Create profile form view (`views/wfm_profile_views.xml`):
  - Contact info: email, phone (editable)
  - Address fields (editable)
  - Professional info: specialty (readonly), hourly rate (editable), VAT
- [x] **T2.5.2** Create server action `action_open_my_profile`
- [x] **T2.5.3** Add security rule for partners to write own partner record
- [x] **T2.5.4** Add "My Profile" menu item

**Deliverable:** Partners can update their contact info and hourly rate

---

### Phase 2.6: Visit Actions (ADDED) - COMPLETE

- [x] **T2.6.1** Add Confirm Visit button (state: assigned -> confirmed)
- [x] **T2.6.2** Add Start Visit button (state: confirmed -> in_progress)
- [x] **T2.6.3** Add Complete Visit button (state: in_progress -> done)
- [x] **T2.6.4** Add Cancel Visit button with confirmation dialog

**Deliverable:** Partners can manage visit lifecycle from their portal

---

### Phase 3: WhatsApp Integration (Hours 9-12) - NOT STARTED

- [ ] **T3.1** Create `wfm_whatsapp` module scaffold:
  - `__manifest__.py` with dependencies (`wfm_core`)
  - Module structure
- [ ] **T3.2** Create Twilio service (`services/twilio_service.py`):
  - Initialize Twilio client with env vars
  - `send_whatsapp(phone, message)` method
  - Error handling and logging
- [ ] **T3.3** Create WhatsApp message model (`models/whatsapp_message.py`):
  - `wfm.whatsapp.message` for logging
  - Fields: `partner_id`, `phone`, `message`, `status`, `sent_at`
- [ ] **T3.4** Extend `wfm.visit` write method:
  - Override `_trigger_notification_agent()` from `wfm_core`
  - Send WhatsApp on partner assignment
- [ ] **T3.5** Add notification templates:
  - Assignment notification
  - Schedule confirmation
  - 24h reminder (via scheduled action)
- [ ] **T3.6** Test WhatsApp notifications with Twilio sandbox

**Deliverable:** Async WhatsApp notifications on status changes

---

### Phase 4: Visit Report Submission (Hours 13-16) - NOT STARTED

- [ ] **T4.1** Create visit report model (`models/visit_report.py`):
  - `wfm.visit.report` model
  - Fields: `visit_id`, `partner_id`, `submitted_at`, `notes`, `attachments`
- [ ] **T4.2** Add report form to visit detail view:
  - Notes field
  - File upload capability
- [ ] **T4.3** Create report submission workflow:
  - Mobile-friendly form
  - Image/document upload
- [ ] **T4.4** Update visit status on report submission:
  - Auto-transition to "Completed" state
  - Trigger SEPE queue (hook for Dev A)
- [ ] **T4.5** Test report submission flow

**Deliverable:** Partners can submit visit reports from the field

---

### Phase 5: Partner Payment Excel Download (Hours 17-20) - NOT STARTED

- [ ] **T5.1** Create payment report wizard (`wizard/payment_report_wizard.py`):
  - Date range selection
  - Partner filter
- [ ] **T5.2** Create Excel export service:
  - Use `xlsxwriter` or `openpyxl`
  - Columns: Visit Date, Client, Location, Hours, Rate, Amount
  - Summary totals at bottom
- [ ] **T5.3** Add payment download to partner menu:
  - Date range filter
  - Download button
- [ ] **T5.4** Create payment report view:
  - List of completed visits with earnings
  - Download Excel button
- [ ] **T5.5** Test Excel generation and download

**Deliverable:** Partners can download payment summary Excel

---

## Module Structure

```
addons/
├── wfm_portal/                      # CREATED
│   ├── __init__.py                  # Done
│   ├── __manifest__.py              # Done
│   ├── models/
│   │   ├── __init__.py              # Done
│   │   └── partner_availability.py  # Done (includes profile action)
│   ├── security/
│   │   ├── ir.model.access.csv      # Done
│   │   └── wfm_portal_security.xml  # Done
│   ├── views/
│   │   ├── wfm_portal_views.xml     # Done
│   │   ├── wfm_availability_views.xml # Done
│   │   ├── wfm_profile_views.xml    # Done
│   │   └── wfm_portal_menus.xml     # Done
│   └── wizard/
│       └── payment_report_wizard.py # Planned
│
└── wfm_whatsapp/                    # PLANNED
    ├── __init__.py
    ├── __manifest__.py
    ├── models/
    │   ├── __init__.py
    │   └── whatsapp_message.py
    ├── services/
    │   ├── __init__.py
    │   └── twilio_service.py
    ├── data/
    │   └── message_templates.xml
    └── security/
        └── ir.model.access.csv
```

---

## Dependencies

| Module | Depends On | Status |
|--------|-----------|--------|
| `wfm_portal` | `base`, `wfm_core` | Deployed |
| `wfm_whatsapp` | `wfm_core` | Planned |

---

## Environment Variables Required

```bash
# For WhatsApp integration (Phase 3)
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

---

## Testing Checklist

### Portal Access - COMPLETE
- [x] Partner can log into Odoo backend
- [x] Partner sees only their own visits
- [x] Visit list shows correct data
- [x] Visit detail page works
- [x] Partner can confirm/start/complete/cancel visits

### Availability - COMPLETE
- [x] Partner can mark unavailable dates
- [x] Calendar displays correctly
- [x] Unavailability saved to database

### My Profile - COMPLETE
- [x] Partner can view their profile
- [x] Partner can edit email, phone, address
- [x] Partner can edit hourly rate
- [x] Specialty is readonly

### WhatsApp - NOT STARTED
- [ ] Twilio credentials configured
- [ ] Assignment triggers WhatsApp message
- [ ] Message logged in database
- [ ] Error handling works

### Report Submission - NOT STARTED
- [ ] Report form accessible in visit detail
- [ ] File upload works
- [ ] Visit status updates on submission

### Payment Excel - NOT STARTED
- [ ] Excel generates correctly
- [ ] Calculations are accurate
- [ ] Download works

---

## Acceptance Criteria

### MVP (24h Demo) - COMPLETE
- [x] Partner can view assignments in backend portal
- [x] Partner can manage visit status
- [x] Partner can update profile
- [x] Basic availability marking works

### Full Implementation - IN PROGRESS (50%)
- [x] Phases 1-2.6 complete
- [ ] WhatsApp notifications
- [ ] Visit report submission
- [ ] Payment Excel download
- [ ] Full test coverage
- [ ] Documentation complete

---

**Last Updated:** 2025-12-13
