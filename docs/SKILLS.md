# WFM System Skills & Capabilities

This document describes what the GEP OHS Workforce Management System can do — the "skills" available to users and agents.

## User Roles

| Role | Description | Primary Skills |
|------|-------------|----------------|
| **Admin** | GEP staff managing clients, contracts, billing | Full system access |
| **Coordinator** | GEP staff scheduling visits | Assignment, Dashboard |
| **Partner** | External OHS professional | Portal, WhatsApp |

---

## Coordinator Skills

### Visit Management

| Skill | Description | Module |
|-------|-------------|--------|
| Create Visit | Schedule new OHS visit for client installation | `wfm_core` |
| Assign Partner | Assign OHS professional to visit | `wfm_core` |
| Smart Assign | AI-recommended partner assignment | `wfm_fsm` |
| Bulk Assign | Assign partner to multiple visits at once | `wfm_fsm` |
| Reschedule Visit | Change visit date/time | `wfm_core` |
| Cancel Visit | Cancel a scheduled visit | `wfm_core` |
| View Visit Details | See full visit information | `wfm_core` |

### Dashboard & Monitoring

| Skill | Description | Module |
|-------|-------------|--------|
| View Dashboard | See color-coded status cards | `wfm_fsm` |
| Filter by State | Filter visits by status (draft, assigned, etc.) | `wfm_fsm` |
| Kanban Board | Drag-drop visit management | `wfm_fsm` |
| Timeline View | See partner schedules over time | `wfm_fsm` |
| View Overdue | Identify visits past due date | `wfm_fsm` |

### Partner Management

| Skill | Description | Module |
|-------|-------------|--------|
| View Partner List | List all OHS partners | `wfm_core` |
| Check Availability | See partner's schedule/conflicts | `wfm_fsm` |
| View Recommendations | See AI-suggested partners for visit | `wfm_fsm` |
| View Relationships | See partner-client history | `wfm_fsm` |
| Send WhatsApp | Send custom message to partner | `wfm_whatsapp` |

### Communication

| Skill | Description | Module |
|-------|-------------|--------|
| Auto-Notify Assignment | System auto-sends WhatsApp on assign | `wfm_whatsapp` |
| Send Custom Message | Compose WhatsApp to partner | `wfm_whatsapp` |
| View Message Log | See sent/received WhatsApp messages | `wfm_whatsapp` |
| Track Delivery | See message delivery status | `wfm_whatsapp` |

---

## Partner Skills

### Portal Access

| Skill | Description | Module |
|-------|-------------|--------|
| View My Visits | See assigned visits list | `wfm_portal` |
| View Visit Details | See client, location, time details | `wfm_portal` |
| Confirm Visit | Accept an assigned visit | `wfm_portal` |
| Manage Availability | Set available/unavailable dates | `wfm_portal` |
| Update Profile | Edit contact information | `wfm_portal` |

### WhatsApp Interaction

| Skill | Description | Module |
|-------|-------------|--------|
| Receive Notifications | Get WhatsApp when assigned | `wfm_whatsapp` |
| Accept via WhatsApp | Reply ACCEPT to confirm | `wfm_whatsapp` |
| Decline via WhatsApp | Reply DENY to decline | `wfm_whatsapp` |
| List Visits | Text "visits" for schedule | `wfm_whatsapp` |
| Get Visit Details | Text "visit 1" for info | `wfm_whatsapp` |
| Get Directions | Receive Google Maps link | `wfm_whatsapp` |

---

## Admin Skills

### Client Management

| Skill | Description | Module |
|-------|-------------|--------|
| Create Client | Add new client company | `wfm_core` |
| Manage Installations | Add/edit client locations | `wfm_core` |
| Create Contract | Set up service agreement | `wfm_core` |
| Define Services | Specify OHS services per installation | `wfm_core` |

### Partner Onboarding

| Skill | Description | Module |
|-------|-------------|--------|
| Create Partner | Add new OHS professional | `wfm_core` |
| Set Specialty | Physician, Safety Engineer, etc. | `wfm_core` |
| Set Hourly Rate | Configure billing rate | `wfm_core` |
| Set Location | City for proximity matching | `wfm_core` |

### Reporting

| Skill | Description | Module |
|-------|-------------|--------|
| Visit Statistics | Completion rates, counts | `wfm_fsm` |
| Partner Performance | Visit counts, ratings | `wfm_fsm` |
| Relationship History | Partner-client visit history | `wfm_fsm` |

---

## System (Autonomous Agent) Skills

### Notification Agent

| Skill | Trigger | Action |
|-------|---------|--------|
| Assignment Notification | Partner assigned to visit | Send WhatsApp with details |
| In-App Notification | Partner assigned | Create Odoo notification |
| 24h Reminder | Daily cron at 9 AM | WhatsApp reminders |
| Delivery Tracking | Twilio callback | Update message status |

### Smart Assignment Engine

| Skill | Input | Output |
|-------|-------|--------|
| Score Partners | Visit ID | Ranked list with scores |
| Calculate Relationship | Partner + Client | 0-100 relationship score |
| Check Availability | Partner + Date | Conflict count |
| Measure Performance | Partner | Completion rate |
| Assess Proximity | Partner + Installation | City match score |
| Balance Workload | Partner | Active assignment count |

### Relationship Tracker

| Skill | Trigger | Action |
|-------|---------|--------|
| Track Visits | Visit completed | Update relationship stats |
| Update Score | Relationship changed | Recalculate 0-100 score |
| Store History | Each visit | First/last visit dates |

---

## Planned Skills (Future)

### AI Chat Integration

| Skill | User Says | System Does |
|-------|-----------|-------------|
| Query Visits | "Show my pending visits" | List visits via LLM |
| Assign Partner | "Assign Dr. X to visit 123" | Execute assignment |
| Check Availability | "Who's free Monday?" | Query and respond |
| Get Stats | "How many visits this week?" | Aggregate and respond |

### SEPE Compliance

| Skill | Description | Status |
|-------|-------------|--------|
| Generate SEPE Report | Export visits for regulator | Planned |
| Validate Compliance | Check service hours vs requirements | Planned |

### Billing Integration

| Skill | Description | Status |
|-------|-------------|--------|
| Calculate Partner Payment | Hours × rate | Planned |
| Generate Invoice | Client billing from visits | Planned |

---

## Skill Matrix by Role

| Skill | Admin | Coordinator | Partner |
|-------|-------|-------------|---------|
| **Visit Management** |
| Create Visit | Yes | Yes | No |
| Assign Partner | Yes | Yes | No |
| Smart Assign | Yes | Yes | No |
| Confirm Visit | Yes | Yes | Yes |
| **Dashboard** |
| View Dashboard | Yes | Yes | No |
| Kanban Board | Yes | Yes | No |
| Timeline View | Yes | Yes | No |
| **Communication** |
| Send WhatsApp | Yes | Yes | No |
| Receive WhatsApp | No | No | Yes |
| Reply via WhatsApp | No | No | Yes |
| **Portal** |
| View My Visits | No | No | Yes |
| Manage Availability | No | No | Yes |
| **Admin** |
| Manage Clients | Yes | No | No |
| Manage Partners | Yes | No | No |
| Manage Contracts | Yes | No | No |

---

## API Skills (MCP Tools)

Available for AI/automation integration:

### Read Operations

```
wfm_list_visits        - Query visits with filters
wfm_get_visit          - Single visit details
wfm_list_partners      - Query partners
wfm_partner_availability - Check availability
wfm_dashboard_data     - Aggregate statistics
wfm_recommendations    - Get smart assignment suggestions
```

### Write Operations

```
wfm_create_visit       - Create new visit
wfm_update_visit       - Update visit fields
wfm_assign_partner     - Assign partner to visit
wfm_confirm_visit      - Confirm visit
wfm_cancel_visit       - Cancel visit
wfm_send_whatsapp      - Send WhatsApp message
```

---

## Skill Invocation Examples

### Coordinator: Smart Assign Flow

```
1. Open visit (draft, no partner)
2. View "Recommended Partners" table
   → System shows top 2 partners with scores
3. Click "Smart Assign" button
   → Wizard opens with detailed breakdown
4. Click "Assign" on preferred partner
   → Partner assigned
   → State changes to "assigned"
   → WhatsApp sent automatically
   → Relationship updated
```

### Partner: WhatsApp Accept Flow

```
1. Partner receives WhatsApp:
   "New visit assigned: Client X on 15/01/2025"
2. Partner replies: "visit 1"
   → System shows full details + Google Maps link
3. Partner replies: "ACCEPT"
   → Visit confirmed
   → Coordinator notified
```

### Coordinator: Bulk Assign Flow

```
1. Select multiple visits in list view
2. Action → "Bulk Assign Partner"
3. Select partner from dropdown
4. Confirm
   → All visits assigned
   → All WhatsApp notifications sent
```
