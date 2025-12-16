# ERPx10 Intelligence & Context Layer Architecture

**Project:** Workforce Management System (WFM)
**Last Updated:** December 2025

---

## ERPx10 Stack Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EVOLVE                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │     CRM      │  │  Accounting  │  │    VoIP      │  │   DeepDoc    │    │
│  │  (SoftOne)   │  │  (Epsilon)   │  │              │  │              │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼──────────────────┼──────────────────┼──────────────────┼──────────┘
          │                  │                  │                  │
          ▼                  ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE / CONTEXT LAYER                              │
│                            (INNOVATE)                                        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      INTELLIGENCE LAYER                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │  AI Chat    │  │  Smart      │  │  Churn      │  │ Autonomous │ │   │
│  │  │  (LLM)      │  │  Assignment │  │  Prediction │  │ Workflows  │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        CONTEXT LAYER                                 │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │ Relationship│  │  Partner    │  │  Workflow   │  │  Message   │ │   │
│  │  │ History     │  │  Health     │  │  Logs       │  │  History   │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ERP CORE (Odoo 19)                                  │
│                              (ADAPT)                                         │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Visits    │  │  Partners   │  │   Clients   │  │  Contracts  │        │
│  │ (wfm.visit) │  │(res.partner)│  │(res.partner)│  │(wfm.contract│        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## WFM Implementation Mapping

### Intelligence Layer Components

| Component | Module | Model/File | Purpose |
|-----------|--------|------------|---------|
| **AI Chat** | `wfm_ai_chat` | `llm_client.py`, `mail_bot.py` | Natural language interface to ERP |
| **Smart Assignment** | `wfm_fsm` | `assignment_engine.py` | AI-powered partner recommendations |
| **Churn Prediction** | `wfm_fsm` | `partner_health.py` | Risk scoring and early warning |
| **AI Retention** | `wfm_fsm` | `ai_retention_engine.py` | Automated retention strategies |
| **Autonomous Workflows** | `wfm_core` | `workflow.py` | Scheduled LLM-driven automation |
| **Tool Executor** | `wfm_ai_chat` | `wfm_tools.py` | 35+ tools for AI to interact with ERP |

### Context Layer Components

| Component | Module | Model | Purpose |
|-----------|--------|-------|---------|
| **Relationship History** | `wfm_fsm` | `wfm.partner.client.relationship` | Partner-client visit history |
| **Partner Health** | `wfm_fsm` | `wfm.partner.health` | Churn risk metrics storage |
| **Workflow Logs** | `wfm_core` | `wfm.workflow.log` | Execution audit trail |
| **WhatsApp Messages** | `wfm_whatsapp` | `wfm.whatsapp.message` | Communication history |
| **Conversation History** | Odoo Core | `mail.message` | Chat context (10 messages) |
| **Partner Availability** | `wfm_portal` | `wfm.partner.availability` | Schedule preferences |

---

## Intelligence Layer Deep Dive

### 1. AI Chat System (`wfm_ai_chat`)

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI CHAT ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────┘

User Message                    LLM (Claude Haiku)               ERP Core
     │                                │                              │
     │  "Assign Dr. Papa to V-123"   │                              │
     ├──────────────────────────────►│                              │
     │                                │  tool_call:                 │
     │                                │  wfm_assign_partner          │
     │                                │  {visit_id:123, partner:5}   │
     │                                ├─────────────────────────────►│
     │                                │                              │
     │                                │◄─────────────────────────────┤
     │                                │  {success: true}             │
     │◄───────────────────────────────┤                              │
     │  "Done! Dr. Papadopoulos       │                              │
     │   assigned to visit #123"      │                              │
```

**Files:**
- `llm_client.py` - LLM API client, context builder, tool orchestration
- `mail_bot.py` - Odoo chat integration, history retrieval
- `wfm_tools.py` - 35+ tool implementations

**Capabilities:**
- Natural language queries (visits, partners, clients)
- Actions (assign, update, cancel, send WhatsApp)
- Multi-round tool execution (up to 5 rounds)
- User context injection (name, date, role)

---

### 2. Smart Assignment Engine (`wfm_fsm`)

```
┌─────────────────────────────────────────────────────────────────┐
│                  SMART ASSIGNMENT SCORING                        │
└─────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │     Visit #123      │
                    │  Client: Vodafone   │
                    │  Date: 2025-12-20   │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  Partner A  │     │  Partner B  │     │  Partner C  │
    │  Dr. Papa   │     │  Dr. Nikos  │     │  Dr. Maria  │
    └─────────────┘     └─────────────┘     └─────────────┘
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────────────────────────────────────────────┐
    │              SCORING ALGORITHM                       │
    │  ┌─────────────────────────────────────────────┐   │
    │  │ Relationship (35%)  │ 30/35 │ 10/35 │  0/35 │   │
    │  │ Availability (25%)  │ 25/25 │ 25/25 │ 25/25 │   │
    │  │ Performance (20%)   │ 18/20 │ 15/20 │ 20/20 │   │
    │  │ Proximity (10%)     │ 10/10 │ 10/10 │  5/10 │   │
    │  │ Workload (10%)      │  7/10 │  5/10 │ 10/10 │   │
    │  ├─────────────────────────────────────────────┤   │
    │  │ TOTAL               │ 90    │ 65    │ 60    │   │
    │  └─────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   RECOMMENDATION    │
                    │  1. Dr. Papa (90)   │
                    │  2. Dr. Nikos (65)  │
                    └─────────────────────┘
```

**File:** `assignment_engine.py`

**Scoring Weights:**
| Factor | Weight | Source |
|--------|--------|--------|
| Relationship | 35% | `wfm.partner.client.relationship` |
| Availability | 25% | Visit conflicts check |
| Performance | 20% | Completion rate, ratings |
| Proximity | 10% | City matching |
| Workload | 10% | Current assignment count |

---

### 3. Churn Prediction System (`wfm_fsm`)

```
┌─────────────────────────────────────────────────────────────────┐
│                   CHURN PREDICTION PIPELINE                      │
└─────────────────────────────────────────────────────────────────┘

     RAW METRICS                SCORING                 OUTPUT
    (30-90 days)              (Weighted)              (Risk Level)

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ visits_last_30d │────►│                 │     │                 │
│ visits_prev_30d │     │  Volume Change  │     │   CRITICAL      │
│                 │     │    (25 pts)     │────►│   (75-100)      │
└─────────────────┘     └─────────────────┘     │                 │
                                                │   Immediate     │
┌─────────────────┐     ┌─────────────────┐     │   Action        │
│ declined_30d    │────►│                 │     └─────────────────┘
│ assigned_30d    │     │  Decline Rate   │
│                 │     │    (30 pts)     │────►┌─────────────────┐
└─────────────────┘     └─────────────────┘     │   HIGH          │
                                                │   (50-74)       │
┌─────────────────┐     ┌─────────────────┐     │                 │
│ days_since_     │────►│                 │     │   Intervention  │
│ last_visit      │     │  Inactivity     │     │   Needed        │
│                 │     │    (20 pts)     │────►└─────────────────┘
└─────────────────┘     └─────────────────┘
                                                ┌─────────────────┐
┌─────────────────┐     ┌─────────────────┐     │   MEDIUM        │
│ payment_        │────►│                 │     │   (30-49)       │
│ complaints      │     │  Issues         │     │                 │
│                 │     │    (15 pts)     │────►│   Monitor       │
└─────────────────┘     └─────────────────┘     └─────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ negative_       │────►│                 │     │   LOW           │
│ feedback        │     │  Feedback       │     │   (0-29)        │
│                 │     │    (10 pts)     │────►│                 │
└─────────────────┘     └─────────────────┘     │   Healthy       │
                                                └─────────────────┘
```

**Files:**
- `partner_health.py` - Metrics storage and scoring
- `ai_retention_engine.py` - AI-generated retention strategies

---

### 4. Autonomous Workflow Engine (`wfm_core`)

```
┌─────────────────────────────────────────────────────────────────┐
│                  WORKFLOW EXECUTION FLOW                         │
└─────────────────────────────────────────────────────────────────┘

  ┌─────────────────┐
  │  Workflow       │
  │  Configuration  │
  │  ┌───────────┐  │
  │  │ schedule  │  │     ┌──────────────┐
  │  │ prompt    │──┼────►│  Scheduler   │
  │  │ tools     │  │     │  (Cron)      │
  │  └───────────┘  │     └──────┬───────┘
  └─────────────────┘            │
                                 │ Trigger
                                 ▼
                        ┌──────────────────┐
                        │  LLM Execution   │
                        │  ┌────────────┐  │
                        │  │ System     │  │
                        │  │ Prompt     │  │
                        │  ├────────────┤  │
                        │  │ Workflow   │  │
                        │  │ Prompt     │  │
                        │  ├────────────┤  │
                        │  │ Tools      │  │
                        │  │ (35+)      │  │
                        │  └────────────┘  │
                        └────────┬─────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
           ▼                     ▼                     ▼
    ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
    │ Tool: List  │      │ Tool: Send  │      │ Tool: Update│
    │ Visits      │      │ WhatsApp    │      │ Status      │
    └─────────────┘      └─────────────┘      └─────────────┘
           │                     │                     │
           └─────────────────────┼─────────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Workflow Log    │
                        │  ┌────────────┐  │
                        │  │ status     │  │
                        │  │ result     │  │
                        │  │ tool_calls │  │
                        │  │ execution  │  │
                        │  │ time       │  │
                        │  └────────────┘  │
                        └──────────────────┘
```

**Files:**
- `workflow.py` - Workflow definition and scheduling
- `workflow_log.py` - Execution audit trail

**Example Workflows:**
| Workflow | Schedule | Prompt |
|----------|----------|--------|
| Morning Reminders | Daily 8 AM | "Send WhatsApp reminders for today's visits" |
| Churn Alert | Weekly Mon | "Identify partners at risk and notify coordinators" |
| SEPE Report | Monthly 1st | "Generate SEPE export for last month" |

---

## Context Layer Deep Dive

### 1. Relationship History (`wfm.partner.client.relationship`)

Stores aggregated visit history between partners and clients for relationship-based recommendations.

```
┌────────────────────────────────────────────────────────────┐
│              RELATIONSHIP CONTEXT RECORD                    │
├────────────────────────────────────────────────────────────┤
│  partner_id: Dr. Papadopoulos (ID: 5)                      │
│  client_id: Vodafone Greece (ID: 12)                       │
├────────────────────────────────────────────────────────────┤
│  total_visits: 45                                          │
│  completed_visits: 42                                      │
│  cancelled_visits: 3                                       │
├────────────────────────────────────────────────────────────┤
│  avg_rating: 4.8 / 5.0                                     │
│  on_time_rate: 95.2%                                       │
├────────────────────────────────────────────────────────────┤
│  first_visit_date: 2023-03-15                              │
│  last_visit_date: 2025-12-10                               │
├────────────────────────────────────────────────────────────┤
│  relationship_score: 87 / 100   ◄── Computed               │
└────────────────────────────────────────────────────────────┘
```

**Used By:** Smart Assignment Engine

---

### 2. Partner Health (`wfm.partner.health`)

Tracks churn risk metrics and computed scores for each partner.

```
┌────────────────────────────────────────────────────────────┐
│               PARTNER HEALTH CONTEXT                        │
├────────────────────────────────────────────────────────────┤
│  partner_id: Dr. Nikos (ID: 8)                             │
│  computed_date: 2025-12-15                                 │
├─────────────────────────┬──────────────────────────────────┤
│  RAW METRICS            │  COMPUTED SCORES                 │
├─────────────────────────┼──────────────────────────────────┤
│  visits_last_30d: 2     │  decline_rate_score: 22/30       │
│  visits_prev_30d: 8     │  volume_change_score: 20/25      │
│  visits_declined: 5     │  inactivity_score: 15/20         │
│  days_since_visit: 21   │  issues_score: 8/15              │
│  payment_complaints: 2  │  feedback_score: 5/10            │
│  negative_feedback: 1   │                                  │
├─────────────────────────┼──────────────────────────────────┤
│                         │  churn_risk_score: 70/100        │
│                         │  risk_level: HIGH                │
└─────────────────────────┴──────────────────────────────────┘
```

**Used By:** Churn Prediction, AI Retention Engine

---

### 3. Workflow Execution Logs (`wfm.workflow.log`)

Audit trail for all autonomous workflow executions.

```
┌────────────────────────────────────────────────────────────┐
│              WORKFLOW LOG CONTEXT                           │
├────────────────────────────────────────────────────────────┤
│  workflow_id: "Morning Reminders"                          │
│  start_time: 2025-12-15 08:00:00                           │
│  end_time: 2025-12-15 08:00:45                             │
│  status: success                                           │
├────────────────────────────────────────────────────────────┤
│  tool_calls: [                                             │
│    {name: "wfm_list_visits", args: {date: "2025-12-15"}},  │
│    {name: "wfm_send_whatsapp", args: {visit_id: 123}},     │
│    {name: "wfm_send_whatsapp", args: {visit_id: 124}},     │
│    {name: "wfm_send_whatsapp", args: {visit_id: 125}},     │
│  ]                                                         │
├────────────────────────────────────────────────────────────┤
│  result_summary: "Sent 3 reminders for today's visits"     │
│  tokens_used: 2,450                                        │
└────────────────────────────────────────────────────────────┘
```

**Used By:** Audit, Debugging, Cost Tracking

---

### 4. Communication History (`wfm.whatsapp.message`)

Log of all WhatsApp notifications sent to partners.

```
┌────────────────────────────────────────────────────────────┐
│              WHATSAPP MESSAGE CONTEXT                       │
├────────────────────────────────────────────────────────────┤
│  visit_id: Visit #123                                      │
│  partner_id: Dr. Papadopoulos                              │
│  phone: +306912345678                                      │
├────────────────────────────────────────────────────────────┤
│  message_type: assignment                                  │
│  message_body: "New visit assigned: Vodafone Athens..."    │
│  status: delivered                                         │
├────────────────────────────────────────────────────────────┤
│  twilio_sid: SM1234567890abcdef                            │
│  sent_at: 2025-12-15 10:30:00                              │
└────────────────────────────────────────────────────────────┘
```

**Used By:** AI Chat (wfm_list_whatsapp_messages), Audit

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTELLIGENCE LAYER DATA FLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────┐
                                    │   USER INPUT    │
                                    │  (Chat/Action)  │
                                    └────────┬────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AI CHAT (LLM Client)                                │
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   System    │    │Conversation │    │    Tool     │    │    User     │  │
│  │   Prompt    │    │   History   │    │   Schema    │    │   Context   │  │
│  │  (Static)   │    │ (10 msgs)   │    │ (35 tools)  │    │  (Dynamic)  │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │          │
│         └──────────────────┴──────────────────┴──────────────────┘          │
│                                    │                                         │
│                                    ▼                                         │
│                          ┌─────────────────┐                                │
│                          │   LLM (Claude)  │                                │
│                          │    via LiteLLM  │                                │
│                          └────────┬────────┘                                │
│                                   │                                         │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  SMART ASSIGNMENT   │  │  CHURN PREDICTION   │  │  AUTONOMOUS         │
│                     │  │                     │  │  WORKFLOWS          │
│  Read:              │  │  Read:              │  │                     │
│  - Relationships    │  │  - Partner Health   │  │  Execute:           │
│  - Visits           │  │  - Visit History    │  │  - Tool calls       │
│  - Partners         │  │                     │  │  - Actions          │
│                     │  │  Compute:           │  │                     │
│  Compute:           │  │  - Risk scores      │  │  Write:             │
│  - Scores           │  │  - AI strategies    │  │  - Workflow logs    │
│  - Recommendations  │  │                     │  │                     │
└──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CONTEXT LAYER                                     │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Relationship   │  │  Partner        │  │  Workflow       │             │
│  │  History        │  │  Health         │  │  Logs           │             │
│  │                 │  │                 │  │                 │             │
│  │  - total_visits │  │  - risk_score   │  │  - tool_calls   │             │
│  │  - avg_rating   │  │  - risk_level   │  │  - status       │             │
│  │  - relationship │  │  - metrics      │  │  - result       │             │
│  │    _score       │  │                 │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  WhatsApp       │  │  Conversation   │  │  Partner        │             │
│  │  Messages       │  │  History        │  │  Availability   │             │
│  │                 │  │                 │  │                 │             │
│  │  - message_body │  │  - mail.message │  │  - blackout     │             │
│  │  - status       │  │  - last 10 msgs │  │    dates        │             │
│  │  - sent_at      │  │                 │  │  - preferences  │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ERP CORE (Odoo 19)                                  │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ wfm.visit   │  │ res.partner │  │wfm.contract │  │ wfm.sepe    │        │
│  │             │  │ (client/    │  │             │  │ .export     │        │
│  │ - state     │  │  partner)   │  │ - services  │  │             │        │
│  │ - date      │  │             │  │ - billing   │  │ - xml_data  │        │
│  │ - partner_id│  │ - specialty │  │             │  │ - status    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Storage Architecture

### At Rest (Database)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POSTGRESQL DATABASE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  INTELLIGENCE LAYER TABLES                                                   │
│  ├── wfm_workflow              # Workflow definitions                       │
│  ├── wfm_workflow_log          # Execution audit trail                      │
│  └── ir_config_parameter       # LLM API keys, model config                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  CONTEXT LAYER TABLES                                                        │
│  ├── wfm_partner_client_relationship  # Partner-client history              │
│  ├── wfm_partner_health               # Churn metrics                       │
│  ├── wfm_whatsapp_message             # Communication log                   │
│  ├── wfm_partner_availability         # Schedule preferences                │
│  └── mail_message                     # Conversation history                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ERP CORE TABLES                                                             │
│  ├── wfm_visit                 # Visit records                              │
│  ├── wfm_installation          # Client locations                           │
│  ├── wfm_contract              # Service contracts                          │
│  ├── wfm_sepe_export           # Compliance exports                         │
│  └── res_partner               # Clients & Partners                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### In Transit (API Calls)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API TRAFFIC FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  Odoo Server                  LiteLLM Proxy                  Claude API
       │                            │                             │
       │  POST /chat/completions    │                             │
       │  {                         │                             │
       │    model: "claude-haiku",  │                             │
       │    messages: [...],        │                             │
       │    tools: [...]            │                             │
       │  }                         │                             │
       ├───────────────────────────►│                             │
       │                            │  POST /v1/messages          │
       │                            ├────────────────────────────►│
       │                            │                             │
       │                            │◄────────────────────────────┤
       │                            │  {tool_calls: [...]}        │
       │◄───────────────────────────┤                             │
       │  {tool_calls: [...]}       │                             │
       │                            │                             │


  Odoo Server                    Twilio API                   WhatsApp
       │                            │                             │
       │  POST /messages.json       │                             │
       │  {                         │                             │
       │    To: "whatsapp:+30...",  │                             │
       │    Body: "New visit..."    │                             │
       │  }                         │                             │
       ├───────────────────────────►│                             │
       │                            │  WhatsApp Business API      │
       │                            ├────────────────────────────►│
       │                            │                             │
       │◄───────────────────────────┤                             │
       │  {sid: "SM123..."}         │                             │
```

---

## Component File Reference

| Layer | Component | File Path | Lines |
|-------|-----------|-----------|-------|
| **Intelligence** | LLM Client | `wfm_ai_chat/models/llm_client.py` | ~1078 |
| **Intelligence** | Mail Bot | `wfm_ai_chat/models/mail_bot.py` | ~207 |
| **Intelligence** | Tool Executor | `wfm_ai_chat/tools/wfm_tools.py` | ~1465 |
| **Intelligence** | Assignment Engine | `wfm_fsm/models/assignment_engine.py` | ~300 |
| **Intelligence** | AI Retention | `wfm_fsm/models/ai_retention_engine.py` | ~574 |
| **Intelligence** | Workflow Engine | `wfm_core/models/workflow.py` | ~400 |
| **Context** | Partner Health | `wfm_fsm/models/partner_health.py` | ~350 |
| **Context** | Relationships | `wfm_fsm/models/partner_relationship.py` | ~200 |
| **Context** | WhatsApp Log | `wfm_whatsapp/models/whatsapp_message.py` | ~250 |
| **Context** | Workflow Log | `wfm_core/models/workflow_log.py` | ~150 |
| **Context** | Availability | `wfm_portal/models/partner_availability.py` | ~100 |

---

## Future Enhancements

### Missing Context Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| `wfm.user.ai.context` | Persistent user memory | High |
| `wfm.conversation.summary` | Summarized chat history | Medium |
| `wfm.user.preference` | User settings storage | Medium |
| `wfm.audit.log` | Comprehensive action logging | Low |

### Missing Intelligence Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| Voice Integration | Speech-to-text for chat | Medium |
| Document AI | PDF/image analysis | Low |
| Predictive Scheduling | ML-based visit optimization | Medium |
| Anomaly Detection | Unusual pattern alerts | Low |

---

## Conclusion

The WFM project implements a two-layer intelligence architecture:

1. **Intelligence Layer** - AI-powered decision making
   - AI Chat with 35+ tools
   - Smart Partner Assignment
   - Churn Prediction
   - Autonomous Workflows

2. **Context Layer** - Persistent knowledge storage
   - Relationship history
   - Health metrics
   - Communication logs
   - Execution audit trails

This architecture serves as the foundation for ERPx10's Innovation layer, demonstrating how AI can be deeply integrated into ERP operations while maintaining clean separation between intelligence (reasoning) and context (memory).
