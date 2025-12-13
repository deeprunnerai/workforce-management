# Autonomous Agent Workflow Engine

**Status:** Proposed
**Module:** `wfm_core` (extension)

## Overview

An engine that allows users to define automated workflows through natural language in Odoo Chat. Workflows are stored as records and executed by cron jobs at specified frequencies.

## Core Concept

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION                              │
│                                                                      │
│  Chat: "Every morning at 9AM, check all draft visits older than     │
│         3 days and send a reminder to coordinators"                  │
│                                                                      │
│  OdooBot: "I've created workflow 'Draft Visit Reminder'              │
│            ✓ Trigger: Daily at 09:00                                 │
│            ✓ Action: List draft visits > 3 days, notify coordinators │
│            Want me to activate it?"                                  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     WORKFLOW STORAGE (Odoo)                          │
│                                                                      │
│  wfm.workflow                                                        │
│  ├── name: "Draft Visit Reminder"                                    │
│  ├── prompt: "Check all draft visits older than 3 days..."          │
│  ├── schedule: "0 9 * * *" (cron expression)                        │
│  ├── active: True                                                    │
│  ├── last_run: 2025-12-13 09:00:00                                  │
│  └── created_by: user_id                                            │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     CRON EXECUTION                                   │
│                                                                      │
│  ir.cron: "WFM Workflow Runner"                                      │
│  ├── Runs every minute                                               │
│  ├── Checks workflows due for execution                              │
│  └── Calls LLM with workflow prompt + tools                          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     AGENT EXECUTION                                  │
│                                                                      │
│  LLM receives: System prompt + Workflow prompt + Tools               │
│  LLM executes: wfm_list_visits → filter → wfm_send_whatsapp         │
│  Result logged to: wfm.workflow.log                                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Models

### wfm.workflow

| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Workflow name |
| `description` | Text | Human-readable description |
| `prompt` | Text | Natural language instruction for LLM |
| `schedule_type` | Selection | `manual`, `interval`, `cron` |
| `cron_expression` | Char | Cron expression (e.g., `0 9 * * *`) |
| `interval_number` | Integer | For interval type (e.g., 4) |
| `interval_type` | Selection | `minutes`, `hours`, `days`, `weeks` |
| `active` | Boolean | Is workflow enabled |
| `last_run` | Datetime | Last execution time |
| `next_run` | Datetime | Computed next run time |
| `run_count` | Integer | Total executions |
| `success_count` | Integer | Successful executions |
| `created_by` | Many2one | User who created via chat |
| `log_ids` | One2many | Execution logs |

### wfm.workflow.log

| Field | Type | Description |
|-------|------|-------------|
| `workflow_id` | Many2one | Parent workflow |
| `started_at` | Datetime | Execution start |
| `ended_at` | Datetime | Execution end |
| `status` | Selection | `running`, `success`, `failed` |
| `prompt_used` | Text | Actual prompt sent to LLM |
| `tool_calls` | Text | JSON of tools called |
| `result` | Text | LLM final response |
| `error` | Text | Error message if failed |
| `tokens_used` | Integer | Token consumption |

## Example Workflows

### 1. Morning Draft Visit Check
```
Trigger: Daily at 09:00
Prompt: "List all visits in draft state. For each visit older than 3 days,
         send a WhatsApp reminder to the assigned coordinator."
```

### 2. End-of-Day SEPE Report
```
Trigger: Daily at 18:00
Prompt: "Find all visits completed today. Group them by client and service
         contract. For each contract with completed visits, invoke the SEPE
         agent to generate the compliance report."
```

### 3. Partner Availability Alert
```
Trigger: Every Monday at 08:00
Prompt: "Check visits scheduled for this week that don't have a partner
         assigned. List them and notify the coordinator team via WhatsApp."
```

### 4. Overdue Visit Escalation
```
Trigger: Every 4 hours
Prompt: "Find visits that are past their scheduled date but not completed.
         If overdue by more than 24 hours, mark as urgent and notify admin."
```

### 5. Weekly Performance Summary
```
Trigger: Every Friday at 17:00
Prompt: "Generate a weekly summary: total visits completed, by partner,
         by client, average completion time. Format as a report."
```

## Chat Commands for Workflow Management

### Creating Workflows
```
User: "Create a workflow that runs every morning at 9AM to check draft visits"
Bot: Creates wfm.workflow record, confirms details

User: "Every Friday, send me a summary of completed visits"
Bot: Creates weekly workflow with user as recipient
```

### Managing Workflows
```
User: "Show my workflows"
Bot: Lists user's workflows with status, last run, next run

User: "Pause the draft reminder workflow"
Bot: Sets active=False on the workflow

User: "Run the SEPE report workflow now"
Bot: Triggers immediate execution, shows result

User: "Delete workflow 'Old Report'"
Bot: Confirms and deletes
```

### Monitoring
```
User: "What did the morning workflow do today?"
Bot: Shows wfm.workflow.log for today's run

User: "Any workflow errors this week?"
Bot: Lists failed executions with errors
```

## New LLM Tools Required

| Tool | Description |
|------|-------------|
| `wfm_create_workflow` | Create a new workflow from natural language |
| `wfm_list_workflows` | List user's workflows |
| `wfm_update_workflow` | Modify workflow (schedule, prompt, active) |
| `wfm_delete_workflow` | Delete a workflow |
| `wfm_run_workflow` | Trigger immediate execution |
| `wfm_workflow_logs` | Get execution history |

## Schedule Types

### Interval-Based
```
"Every 4 hours"     → interval_number=4, interval_type='hours'
"Every 30 minutes"  → interval_number=30, interval_type='minutes'
"Every 2 days"      → interval_number=2, interval_type='days'
```

### Cron-Based
```
"Every day at 9AM"       → 0 9 * * *
"Every Monday at 8AM"    → 0 8 * * 1
"First of every month"   → 0 9 1 * *
"Every hour"             → 0 * * * *
```

### Event-Based (Future)
```
"When a visit is marked complete"  → Triggered by write() override
"When a new client is created"     → Triggered by create() override
```

## Implementation Phases

### Phase 1: Core Engine
- [ ] `wfm.workflow` model
- [ ] `wfm.workflow.log` model
- [ ] Cron job runner
- [ ] Basic execution (call LLM with prompt)

### Phase 2: Chat Integration
- [ ] Workflow creation via chat
- [ ] Natural language to schedule parsing
- [ ] Workflow management commands
- [ ] Execution result reporting

### Phase 3: Advanced Features
- [ ] Event-based triggers
- [ ] Workflow chaining (output of one → input of next)
- [ ] Conditional execution
- [ ] Approval workflows (human-in-the-loop)

### Phase 4: SEPE Agent Integration
- [ ] `wfm_invoke_sepe_agent` tool
- [ ] Report generation workflows
- [ ] Compliance tracking automation

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| Runaway workflows | Max 100 tool calls per execution |
| Resource abuse | Rate limiting per user |
| Privilege escalation | Workflows run with creator's permissions |
| Sensitive data | Log redaction for PII |
| Infinite loops | Execution timeout (5 minutes max) |

## Cost Estimation

| Scenario | Workflows | Runs/Day | LLM Calls | Monthly Cost |
|----------|-----------|----------|-----------|--------------|
| Small | 5 | 10 | ~50 | ~$5 |
| Medium | 20 | 50 | ~250 | ~$25 |
| Large | 50 | 200 | ~1000 | ~$100 |

Based on Claude Haiku pricing (~$0.001 per request average).

## Architecture Decision

**Option A: Extend wfm_core**
- Workflows are core WFM functionality
- Tight integration with existing models
- Single module to maintain

**Option B: Separate wfm_workflow module**
- Cleaner separation of concerns
- Can be disabled independently
- More modular

**Recommendation:** Start in `wfm_core`, extract to `wfm_workflow` if it grows complex.

## Example: Creating a Workflow via Chat

```
User: "I want to automate checking for unassigned visits every morning"

Bot: "I'll help you create that workflow. Let me confirm the details:

     📋 **New Workflow**
     • Name: Unassigned Visit Check
     • Schedule: Daily at 09:00
     • Action: List visits without partners, notify coordinator

     Should I create this workflow?"

User: "Yes, but make it run at 8:30 instead"

Bot: "✅ Workflow created!

     • Name: Unassigned Visit Check
     • Schedule: Daily at 08:30
     • Status: Active
     • Next run: Tomorrow at 08:30

     I'll check for unassigned visits every morning and let you know."
```

## Next Steps

1. Review and approve this design
2. Create `wfm.workflow` and `wfm.workflow.log` models
3. Implement cron runner
4. Add workflow tools to `wfm_ai_chat`
5. Test with simple workflows
6. Integrate SEPE agent
