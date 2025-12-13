# WFM System Skills & Capabilities

This document describes what the GEP OHS Workforce Management System can do — the "skills" available to users and agents.

## User Roles

| Role | Description | Primary Skills |
|------|-------------|----------------|
| **Admin** | GEP staff managing clients, contracts, billing | Full system access |
| **Coordinator** | GEP staff scheduling visits | Assignment, Dashboard, Churn Analysis |
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

### Churn Analysis

| Skill | Description | Module |
|-------|-------------|--------|
| View At-Risk Partners | See partners at churn risk | `wfm_fsm` |
| Check Partner Health | View detailed risk scoring | `wfm_fsm` |
| Log Retention Action | Record retention interventions | `wfm_fsm` |
| Resolve Retention Ticket | Close retention cases | `wfm_fsm` |
| View Churn Dashboard | Analytics and trends | `wfm_fsm` |
| Get AI Strategy | AI-powered retention recommendations | `wfm_fsm` |

### Communication

| Skill | Description | Module |
|-------|-------------|--------|
| Auto-Notify Assignment | System auto-sends WhatsApp on assign | `wfm_whatsapp` |
| Send Custom Message | Compose WhatsApp to partner | `wfm_whatsapp` |
| View Message Log | See sent/received WhatsApp messages | `wfm_whatsapp` |
| Track Delivery | See message delivery status | `wfm_whatsapp` |

### AI Chat

| Skill | Description | Module |
|-------|-------------|--------|
| Query Visits | Ask questions about visits | `wfm_ai_chat` |
| Assign via Chat | "Assign Dr. X to visit 123" | `wfm_ai_chat` |
| Check Availability | "Who's free Monday?" | `wfm_ai_chat` |
| Get Stats | "How many visits this week?" | `wfm_ai_chat` |
| Churn Queries | "Show at-risk partners" | `wfm_ai_chat` |

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

### SEPE Compliance

| Skill | Description | Module |
|-------|-------------|--------|
| Create SEPE Export | Generate compliance report | `wfm_core` |
| View Export History | Track previous exports | `wfm_core` |
| Download Export File | Get SEPE-formatted file | `wfm_core` |

### Billing

| Skill | Description | Module |
|-------|-------------|--------|
| View Billing Overview | Dashboard with billing stats | `wfm_core` |
| Filter Not Billed | See unbilled visits | `wfm_core` |
| Filter Invoiced | See invoiced visits | `wfm_core` |
| Filter Client Paid | See paid visits | `wfm_core` |
| Filter Settled | See fully settled visits | `wfm_core` |

### Automation

| Skill | Description | Module |
|-------|-------------|--------|
| Create Workflow | Define trigger-based automation | `wfm_core` |
| View Execution Logs | Track workflow runs | `wfm_core` |
| Enable/Disable Workflow | Control automation status | `wfm_core` |

### Reporting

| Skill | Description | Module |
|-------|-------------|--------|
| Visit Statistics | Completion rates, counts | `wfm_fsm` |
| Partner Performance | Visit counts, ratings | `wfm_fsm` |
| Relationship History | Partner-client visit history | `wfm_fsm` |
| Churn Analytics | Risk distribution, trends | `wfm_fsm` |

---

## System (Autonomous Agent) Skills

### Notification Agent

| Skill | Trigger | Action |
|-------|---------|--------|
| Assignment Notification | Partner assigned to visit | Send WhatsApp with details |
| In-App Notification | Partner assigned | Create Odoo notification |
| 24h Reminder | Daily cron at 9 AM | WhatsApp reminders |
| Delivery Tracking | Twilio callback | Update message status |

### Workflow Engine

| Skill | Trigger | Action |
|-------|---------|--------|
| Field Change Trigger | Record field updates | Execute configured actions |
| Send WhatsApp | Workflow action | Send templated message |
| Update Fields | Workflow action | Modify record values |
| Call Webhook | Workflow action | HTTP POST to URL |
| Log Execution | Every workflow run | Record in audit log |

### Smart Assignment Engine

| Skill | Input | Output |
|-------|-------|--------|
| Score Partners | Visit ID | Ranked list with scores |
| Calculate Relationship | Partner + Client | 0-100 relationship score |
| Check Availability | Partner + Date | Conflict count |
| Measure Performance | Partner | Completion rate |
| Assess Proximity | Partner + Installation | City match score |
| Balance Workload | Partner | Active assignment count |

### Churn Analysis Engine

| Skill | Input | Output |
|-------|-------|--------|
| Compute Partner Health | Partner ID | Health score (0-100) |
| Classify Risk Level | Health score | low/medium/high/critical |
| Identify At-Risk | Threshold | List of at-risk partners |
| Generate Strategy | Partner health data | AI retention recommendations |
| Track Interventions | Actions taken | Intervention history |

### Relationship Tracker

| Skill | Trigger | Action |
|-------|---------|--------|
| Track Visits | Visit completed | Update relationship stats |
| Update Score | Relationship changed | Recalculate 0-100 score |
| Store History | Each visit | First/last visit dates |

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
| **Churn Analysis** |
| View At-Risk Partners | Yes | Yes | No |
| Log Retention Action | Yes | Yes | No |
| View Churn Dashboard | Yes | Yes | No |
| **Communication** |
| Send WhatsApp | Yes | Yes | No |
| Receive WhatsApp | No | No | Yes |
| Reply via WhatsApp | No | No | Yes |
| **AI Chat** |
| Query System | Yes | Yes | No |
| Execute Actions | Yes | Yes | No |
| **Portal** |
| View My Visits | No | No | Yes |
| Manage Availability | No | No | Yes |
| **Admin** |
| Manage Clients | Yes | No | No |
| Manage Partners | Yes | No | No |
| Manage Contracts | Yes | No | No |
| SEPE Exports | Yes | No | No |
| Billing Dashboard | Yes | No | No |
| Automation | Yes | No | No |

---

## API Skills (AI Chat Tools)

Available for AI/automation integration:

### Visit Operations

```
wfm_list_visits        - Query visits with filters
wfm_get_visit          - Single visit details
wfm_create_visit       - Create new visit
wfm_update_visit       - Update visit fields
wfm_assign_partner     - Assign partner to visit
wfm_confirm_visit      - Confirm visit
wfm_cancel_visit       - Cancel visit
```

### Partner Operations

```
wfm_list_partners      - Query partners
wfm_partner_availability - Check availability
wfm_recommendations    - Get smart assignment suggestions
```

### Churn Analysis Operations

```
wfm_list_at_risk_partners    - Query at-risk partners
wfm_get_partner_health       - Detailed health analysis
wfm_log_retention_action     - Log intervention
wfm_resolve_retention_ticket - Close retention case
wfm_churn_dashboard_stats    - Dashboard statistics
wfm_get_ai_retention_strategy - AI recommendations
wfm_run_churn_computation    - Trigger health calculation
```

### Dashboard & Communication

```
wfm_dashboard_data     - Aggregate statistics
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

### Coordinator: Churn Analysis Flow

```
1. Navigate to Analysis → Churn Analytics
2. View dashboard with risk distribution
3. Click "High Risk" card to see at-risk partners
4. Open partner health record
5. Click "Get AI Strategy" for recommendations
6. Log retention action taken
7. Follow up and resolve ticket
```

### AI Chat: Query Example

```
User: "Show me partners at high churn risk"
AI: Uses wfm_list_at_risk_partners tool
AI: "Found 5 partners at high risk:
    1. Dr. Papadopoulos (score: 28)
    2. Eng. Nikolaou (score: 32)
    ..."

User: "What's the retention strategy for Dr. Papadopoulos?"
AI: Uses wfm_get_ai_retention_strategy tool
AI: "Recommended strategy:
    - Schedule 1:1 call within 48 hours
    - Offer priority assignment for preferred clients
    - Review compensation structure..."
```
