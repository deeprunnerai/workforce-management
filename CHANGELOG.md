# Changelog

All notable changes to the GEP OHS Workforce Management System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- Initial project structure with `addons/wfm_core/` directory
- `CLAUDE.md` - Project context for AI-assisted development
- `PLAN.md` - Dev A implementation approach
- `TASKS.md` - Detailed task breakdown (39 tasks, 8 phases)
- `STATUS.md` - Progress tracking template
- Git branches: `main`, `dev-a`, `dev-b`, `dev-c`

### @gauravdr (Core Models) - In Progress
- [ ] `res.partner` extension (client/partner flags)
- [ ] `wfm.installation` model
- [ ] `wfm.visit.stage` model
- [ ] `wfm.visit` model
- [ ] Seed data (10 clients, 50 installations, 100 partners, 200 visits)

### @riya-2098 (Kanban/Dashboard) - Pending
- [ ] Kanban pipeline view
- [ ] Dashboard with 4 color cards
- [ ] Stage drag-drop functionality

### @PanosAndr (Portal/WhatsApp) - Pending
- [ ] Partner portal (view-only)
- [ ] WhatsApp notification agent
- [ ] Twilio integration

---

## [0.1.0] - TBD

### Added
- Initial release of wfm_core module
- Client and Partner management
- Installation tracking
- Visit scheduling with Kanban stages
- Autonomous notification agent

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | TBD | MVP Release - 12h Sprint |

---

## Contributors

| Dev | GitHub | Email | Scope |
|-----|--------|-------|-------|
| **Dev A** | [@gauravdr](https://github.com/gauravdr) | gaurav@deeprunner.ai | Core models, seed data |
| **Dev B** | [@riya-2098](https://github.com/riya-2098) | r.verma@deeprunner.ai | Kanban, dashboard |
| **Dev C** | [@PanosAndr](https://github.com/PanosAndr) | p.andrikopoulos@deeprunner.ai | Portal, WhatsApp |
