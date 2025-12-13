# AI Chat Integration for WFM Odoo

**Status: Implemented** - Module `wfm_ai_chat` created

## Overview

Integrate an LLM-powered conversational assistant into Odoo's built-in chat interface via OdooBot. Users (coordinators, admins, partners) can interact naturally with the system to query data and perform actions without navigating complex menus.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Odoo Frontend                                │
│                    (Built-in Discuss/Chat UI)                        │
│                         OdooBot Chat                                 │
└─────────────────────┬───────────────────────────────────────────────┘
                      │ User sends message to OdooBot
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    wfm_ai_chat Module (Odoo)                         │
│  - Overrides mail.bot._get_answer()                                  │
│  - Intercepts messages when user is in 'idle' state                  │
│  - Calls LiteLLM Proxy via OpenAI-compatible API                     │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LiteLLM Proxy                                   │
│              https://prod.litellm.deeprunner.ai                      │
│                 (claude-3-5-haiku-latest)                            │
│  - Receives system prompt + user message + tool definitions          │
│  - Returns tool calls or text response                               │
└─────────────────────┬───────────────────────────────────────────────┘
                      │ Tool calls
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 WfmToolExecutor (Python)                             │
│  - wfm_list_visits, wfm_get_visit                                    │
│  - wfm_list_partners, wfm_list_clients                               │
│  - wfm_assign_partner, wfm_update_visit                              │
│  - wfm_dashboard_stats                                               │
│  - Executes Odoo ORM operations                                      │
│  - Returns structured results to LLM                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
addons/wfm_ai_chat/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── mail_bot.py          # Overrides OdooBot
│   └── llm_client.py        # LiteLLM API client
├── tools/
│   ├── __init__.py
│   └── wfm_tools.py         # Tool executor
├── security/
│   └── ir.model.access.csv
└── data/
    └── ir_config_parameter.xml
```

## What Users Can Do

### Coordinator Queries (Read)

| Natural Language | Tool Called | Example Response |
|------------------|-------------|------------------|
| "Show my pending visits for this week" | `wfm_list_visits` | List of 5 visits with dates, clients, status |
| "Who is available on Monday in Athens?" | `wfm_partner_availability` | 3 partners with specialties |
| "How many visits did we complete last month?" | `wfm_visit_stats` | 42 completed, 3 cancelled |
| "Which partners work with Cosmote?" | `wfm_partner_client_relationships` | Partners + visit history |

### Coordinator Actions (Write)

| Natural Language | Tool Called | Action |
|------------------|-------------|--------|
| "Assign Dr. Papadopoulos to visit #123" | `wfm_assign_partner` | Updates visit, triggers notification |
| "Reschedule visit #456 to next Tuesday" | `wfm_update_visit` | Changes date, notifies partner |
| "Create a visit for Vodafone installation in Thessaloniki" | `wfm_create_visit` | Creates draft visit |
| "Cancel visit #789" | `wfm_cancel_visit` | Sets state to cancelled |

### Partner Self-Service

| Natural Language | Tool Called | Action |
|------------------|-------------|--------|
| "What visits do I have this week?" | `wfm_my_visits` | Partner's schedule |
| "Confirm visit #123" | `wfm_confirm_visit` | Changes state to confirmed |
| "I need to reschedule Thursday's visit" | `wfm_request_reschedule` | Creates change request |

### Admin Queries

| Natural Language | Tool Called | Response |
|------------------|-------------|----------|
| "Show dashboard summary" | `wfm_dashboard_data` | Counts by state, alerts |
| "List all partners in Athens" | `wfm_list_partners` | Filtered partner list |
| "Which clients have overdue visits?" | `wfm_overdue_visits` | Clients with compliance issues |

## WFM-Specific Tools to Implement

### Visit Management
- `wfm_list_visits` - Filter by date, state, partner, client
- `wfm_get_visit` - Single visit details
- `wfm_create_visit` - Create new visit
- `wfm_update_visit` - Update fields (date, time, notes)
- `wfm_assign_partner` - Assign partner (triggers notification)
- `wfm_cancel_visit` - Cancel with reason
- `wfm_confirm_visit` - Partner confirms

### Partner Management
- `wfm_list_partners` - Filter by specialty, city, availability
- `wfm_partner_availability` - Check availability for date/time
- `wfm_partner_schedule` - Partner's upcoming visits
- `wfm_get_recommendations` - Smart assignment suggestions

### Client & Installation
- `wfm_list_clients` - Search clients
- `wfm_client_installations` - Installations for a client
- `wfm_client_visits` - Visit history for client

### Dashboard & Reporting
- `wfm_dashboard_data` - Aggregate statistics
- `wfm_visit_stats` - Completion rates, averages
- `wfm_partner_performance` - Partner metrics

## Productivity Improvements

### Before (Manual Navigation)
1. Open Odoo
2. Navigate to Visits menu
3. Apply filters (date, state)
4. Scroll through list
5. Click visit to open
6. Click Edit
7. Select partner from dropdown
8. Save
9. **~2-3 minutes per assignment**

### After (AI Chat)
1. Type: "Assign Papadopoulos to visit 123"
2. **~5 seconds**

### Time Savings Estimate

| Task | Manual | AI Chat | Savings |
|------|--------|---------|---------|
| Assign partner | 2 min | 10 sec | 92% |
| Check availability | 3 min | 15 sec | 92% |
| View week schedule | 1 min | 10 sec | 83% |
| Create visit | 3 min | 30 sec | 83% |
| Dashboard check | 30 sec | 5 sec | 83% |

**For a coordinator doing 20 assignments/day:**
- Manual: 40 minutes
- AI Chat: 3 minutes
- **Daily savings: 37 minutes**

### Qualitative Benefits

1. **Reduced Training** - New coordinators productive faster
2. **Mobile-Friendly** - Chat works better on phones than full UI
3. **Hands-Free** - Voice-to-text possible
4. **Context Switching** - Stay in chat, don't jump between screens
5. **Natural Language** - No need to learn Odoo navigation

## Caveats & Considerations

### Technical Caveats

| Issue | Impact | Mitigation |
|-------|--------|------------|
| **LLM Latency** | 1-3 sec per request | Cache common queries, show typing indicator |
| **Hallucination** | AI might suggest non-existent records | Validate all IDs before operations |
| **Token Costs** | Haiku is cheap but not free | Rate limiting, caching |
| **Context Limits** | Can't show 1000 visits in chat | Paginate, summarize |

### Security Concerns

| Risk | Mitigation |
|------|------------|
| **Permission Bypass** | Tools must check `env.user` permissions |
| **SQL Injection** | Use ORM only, never raw SQL |
| **Data Leakage** | Filter results by user's allowed records |
| **Prompt Injection** | Sanitize user input, use system prompts |

### UX Challenges

| Challenge | Solution |
|-----------|----------|
| **Ambiguous Requests** | AI asks clarifying questions |
| **Complex Queries** | Break into multi-step conversation |
| **Error Messages** | User-friendly explanations, not stack traces |
| **Offline** | Graceful degradation message |

### Limitations

1. **No File Uploads** - Can't attach reports via chat (yet)
2. **No Bulk Operations** - One action at a time
3. **No Complex Filtering** - "Show visits where duration > 2h AND city=Athens AND partner NOT assigned" might fail
4. **No Real-time Updates** - Must refresh to see changes from other users

## Implementation Phases

### Phase 1: Read-Only Queries
- `wfm_list_visits`, `wfm_get_visit`
- `wfm_list_partners`, `wfm_partner_availability`
- `wfm_dashboard_data`
- **Risk: Low** - No data modification

### Phase 2: Basic Actions
- `wfm_assign_partner`
- `wfm_update_visit` (date/time only)
- `wfm_confirm_visit`
- **Risk: Medium** - Reversible operations

### Phase 3: Full CRUD
- `wfm_create_visit`
- `wfm_cancel_visit`
- Partner management
- **Risk: Higher** - Need confirmation dialogs

## Cost Estimate

### LiteLLM + Claude Haiku

| Metric | Value |
|--------|-------|
| Input tokens | ~$0.25/MTok |
| Output tokens | ~$1.25/MTok |
| Avg request | ~500 input, ~200 output |
| Cost per request | ~$0.0004 |
| 1000 requests/day | ~$0.40/day |
| Monthly (30 days) | **~$12/month** |

### Infrastructure
- LiteLLM Proxy: Already deployed
- No additional servers needed
- Odoo module: Development time only

## Alternative Approaches Considered

| Approach | Pros | Cons |
|----------|------|------|
| **Embedded in Odoo (chosen)** | Native feel, user permissions, no new UI | Requires Odoo module |
| **Standalone Web App** | Easier to build | Another login, no Odoo context |
| **WhatsApp Bot** | Already have Twilio | Limited UI, security concerns |
| **VS Code / CLI** | Developer-friendly | Not for non-technical users |

## Installation & Configuration

### 1. Install the module

```bash
# Copy to addons
cp -r addons/wfm_ai_chat /opt/odoo/addons/

# Install Python dependency
pip install openai

# Restart Odoo
docker restart odoo
```

### 2. Install via Odoo UI

1. Go to Apps
2. Update Apps List
3. Search for "WFM AI Chat"
4. Click Install

### 3. Configure API Key

Set the LiteLLM API key in Odoo:

```bash
# Via Odoo shell
odoo shell
>>> env['ir.config_parameter'].set_param('wfm_ai_chat.litellm_api_key', 'sk-YOUR-API-KEY')
>>> env.cr.commit()
```

Or via Settings > Technical > System Parameters:
- Key: `wfm_ai_chat.litellm_api_key`
- Value: `sk-nJE8QNo249xmGq1KMFJAIw`

### 4. Start chatting

1. Open Discuss
2. Click on OdooBot in Direct Messages
3. Type any question about visits, partners, or clients

## Implemented Tools

| Tool | Status | Description |
|------|--------|-------------|
| `wfm_list_visits` | Done | Filter by date, state, partner, client |
| `wfm_get_visit` | Done | Get single visit details |
| `wfm_list_partners` | Done | Filter by specialty, city, availability |
| `wfm_list_clients` | Done | Search clients by name |
| `wfm_assign_partner` | Done | Assign partner (triggers notification) |
| `wfm_update_visit` | Done | Update date, time, notes |
| `wfm_dashboard_stats` | Done | Aggregate statistics |

## Next Steps

1. ~~Create `wfm_ai_chat` Odoo module skeleton~~ Done
2. ~~Implement mail.bot override~~ Done
3. ~~Add tool definitions (LLM function calling)~~ Done
4. ~~Build tool executor with Odoo ORM~~ Done
5. Deploy to production and test
6. Add conversation memory (session-based)
7. Implement additional tools (create visit, cancel visit)
8. Add role-based tool restrictions
