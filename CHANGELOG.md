# Changelog

All notable changes to the GEP OHS Workforce Management System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.0.0] - 2025-12-13

### Added

#### wfm_core (19.0.1.0.0)
- `res.partner` extension with client/partner flags
- `wfm.installation` model for client locations
- `wfm.visit.stage` model for Kanban pipeline
- `wfm.visit` model with state workflow
- `wfm.contract` and `wfm.contract.service` models
- Seed data: 10 clients, 50 installations, 100 partners, 200 visits

#### wfm_fsm (19.0.2.0.0)
- Kanban pipeline with drag-drop
- Coordinator dashboard with color-coded cards
- Calendar and Timeline views
- Smart Assignment Engine with AI scoring
- Partner-Client relationship tracking

#### wfm_portal (19.0.1.0.0)
- Backend partner portal
- Security group `group_wfm_partner`
- Partner visit views (list, form, kanban, calendar)
- Partner availability calendar
- My Profile feature
- Visit actions (Confirm/Start/Complete/Cancel)

#### wfm_whatsapp (19.0.1.0.0)
- Twilio REST API integration
- Webhook endpoint for incoming WhatsApp messages
- Auto-notification on partner assignment
- Partner commands: `help`, `visits`, `status`, `visit N`
- Visit actions: `visit N accept`, `visit N deny`
- Google Maps links in visit details
- Message logging and audit trail

### Fixed
- Draft visits no longer visible to partners in portal

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2025-12-13 | MVP Release with WhatsApp integration |

---

## Contributors

| Dev | GitHub | Email | Scope |
|-----|--------|-------|-------|
| **Dev A** | [@gauravdr](https://github.com/gauravdr) | gaurav@deeprunner.ai | Core models, seed data |
| **Dev B** | [@riya-2098](https://github.com/riya-2098) | r.verma@deeprunner.ai | Kanban, dashboard |
| **Dev C** | [@PanosAndr](https://github.com/PanosAndr) | p.andrikopoulos@deeprunner.ai | Portal, WhatsApp |
