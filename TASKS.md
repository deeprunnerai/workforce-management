# WFM Tasks

**Last Updated:** 2025-12-13

---

## Completed Tasks

### Core System (wfm_core)
- [x] Visit model with state workflow
- [x] Client and Installation models
- [x] Partner model extension
- [x] Contract and Contract Service models
- [x] Visit stages configuration
- [x] Notification trigger hooks

### Coordinator Tools (wfm_fsm)
- [x] Kanban pipeline with drag-drop
- [x] Coordinator dashboard with color-coded cards
- [x] Calendar view for visits
- [x] Timeline views (OCA web_timeline)
- [x] Partner-Client relationship model
- [x] AI scoring algorithm (5 weighted factors)
- [x] Smart Assignment wizard with Top 2 recommendations
- [x] Form view recommendations with AI reasoning

### Partner Portal (wfm_portal)
- [x] Backend portal module scaffold
- [x] Security group `group_wfm_partner`
- [x] Record rules for own visits only
- [x] Partner visit views (list, form, kanban, calendar)
- [x] Partner availability calendar
- [x] My Profile feature
- [x] Visit actions (Confirm/Start/Complete/Cancel)
- [x] Bug fix: Hide Draft visits from partners

### Menu & Navigation
- [x] Flat dropdown structure (Dashboard, Visits, Partners, Clients, Config)
- [x] Filtered partner views (Physicians, Engineers)
- [x] Visits by Client view
- [x] Timeline views under each dropdown
- [x] Cleaned up duplicate menu items

### Deployment
- [x] All modules deployed to production
- [x] All branches synced (main, dev-a, dev-b, dev-c)
- [x] Demo credentials configured

---

## In Progress

### Partner Account Creation
- [ ] Create remaining 94 partner user accounts
- [ ] Add WFM Partner group to all partner users
- **Status:** 6/100 created

---

## Pending Tasks

### High Priority

#### WhatsApp Integration (wfm_whatsapp)
- [ ] Create module scaffold with Twilio dependency
- [ ] Create Twilio service (`services/twilio_service.py`)
- [ ] Create WhatsApp message log model
- [ ] Override `_trigger_notification_agent()` from wfm_core
- [ ] Add notification templates (assignment, confirmation, 24h reminder)
- [ ] Test with Twilio sandbox
- [ ] Deploy to production

### Medium Priority

#### Visit Report Submission
- [ ] Create `wfm.visit.report` model
- [ ] Add report form to visit detail view
- [ ] File upload capability for attachments
- [ ] Auto-transition to completed state on submission
- [ ] Test report submission flow

#### Payment Excel Download
- [ ] Create payment report wizard
- [ ] Excel export with visit details and earnings
- [ ] Date range filter
- [ ] Add download to partner menu
- [ ] Test Excel generation

### Low Priority

#### SEPE Export
- [ ] Research SEPE format requirements
- [ ] Create export wizard
- [ ] Generate compliance reports

#### Data Quality
- [ ] Seed additional test data
- [ ] Validate all visit states
- [ ] Test full workflow end-to-end

---

## Task Priority Order

1. **WhatsApp Integration** - Critical for partner notifications
2. **Partner Account Creation** - Needed for demo
3. **Visit Report Submission** - Completes partner workflow
4. **Payment Excel Download** - Partner earnings visibility
5. **SEPE Export** - Future compliance feature

---

## Environment Variables Needed

```bash
# For WhatsApp integration
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

---

## Quick Commands

```bash
# Upgrade modules on production
ssh gaurav-vm "cd /opt/odoo/workforce-management && git pull && cp -r addons/* /opt/odoo/addons/"
ssh gaurav-vm "cd /opt/odoo && docker-compose restart odoo"

# Check branch status
git branch -vv

# Sync all branches
for b in dev-a dev-b dev-c; do git checkout $b && git merge main && git push origin $b; done
```
