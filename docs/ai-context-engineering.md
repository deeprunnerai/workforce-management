# AI Context Engineering & Pipeline Architecture

**Module:** `wfm_ai_chat`
**Status:** Production
**Last Updated:** December 2025

## Overview

This document explains how the WFM AI Chat system builds, manages, and processes context for each conversation. Understanding context engineering is critical for optimizing AI performance, reducing costs, and improving response quality.

---

## Context Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER MESSAGE FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

   ┌──────────────┐         ┌──────────────────┐         ┌──────────────────┐
   │  Odoo Chat   │ ──────► │   mail.bot       │ ──────► │   LLM Client     │
   │   (User)     │         │   (Intercept)    │         │   (API Call)     │
   └──────────────┘         └──────────────────┘         └──────────────────┘
                                    │                            │
                                    ▼                            ▼
                            ┌──────────────────┐         ┌──────────────────┐
                            │ Conversation     │         │ Context Builder  │
                            │ History (10 msg) │         │ (Per Request)    │
                            └──────────────────┘         └──────────────────┘
                                                                 │
                                    ┌────────────────────────────┼────────────────────────────┐
                                    │                            │                            │
                                    ▼                            ▼                            ▼
                            ┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
                            │ System Prompt    │         │ Tools Schema     │         │ User Context     │
                            │ (~400 tokens)    │         │ (~3000 tokens)   │         │ (Dynamic)        │
                            └──────────────────┘         └──────────────────┘         └──────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONTEXT COMPOSITION                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      LLM API REQUEST PAYLOAD                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  messages: [                                                                 │
│    {                                                                         │
│      "role": "system",                                                       │
│      "content": "You are an AI assistant for GEP OHS..."  ◄── System Prompt │
│    },                                                                        │
│    {                                                                         │
│      "role": "user",                                                         │
│      "content": "Show my visits"                          ◄── History[0]    │
│    },                                                                        │
│    {                                                                         │
│      "role": "assistant",                                                    │
│      "content": "Here are your visits..."                 ◄── History[1]    │
│    },                                                                        │
│    ...                                                     ◄── Up to 10 msgs │
│    {                                                                         │
│      "role": "user",                                                         │
│      "content": "Assign partner to visit 5"               ◄── Current msg   │
│    }                                                                         │
│  ],                                                                          │
│  tools: [                                                                    │
│    { "function": { "name": "wfm_list_visits", ... } },    ◄── 35+ Tools     │
│    { "function": { "name": "wfm_assign_partner", ... } },                    │
│    ...                                                                       │
│  ]                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Context Components

### 1. System Prompt (~400 tokens)

**Source:** `llm_client.py:_get_system_prompt()`

The system prompt is regenerated fresh for every request with dynamic user context:

```python
def _get_system_prompt(self):
    user = self.env.user          # Current logged-in user
    today = str(self.env.cr.now().date())

    return f"""You are an AI assistant for the GEP OHS Workforce Management System.
You help coordinators, admins, and partners manage OHS visits.

Current user: {user.name}         # Dynamic: "Gaurav Sharma" or "Panos Andrikopoulos"
Current date: {today}             # Dynamic: "2025-12-15"

You have access to these tools:
- wfm_list_visits: List visits with optional filters
- wfm_assign_partner: Assign a partner to a visit
... (35+ tools listed)

Guidelines:
1. Always be helpful and concise
2. Format dates in DD/MM/YYYY format for Greek users
3. Confirm actions before making changes
"""
```

**What's Injected:**
| Element | Source | Example |
|---------|--------|---------|
| User Name | `self.env.user.name` | "Gaurav Sharma" |
| User Role | Implicit (same tools) | Admin/Coordinator/Partner |
| Current Date | `self.env.cr.now()` | "2025-12-15" |
| Tool List | Static in prompt | 35+ tool descriptions |

---

### 2. Tools Schema (~3000 tokens)

**Source:** `llm_client.py:_get_tools_schema()`

The tools schema defines all available function calls. This is **static** and sent with every request:

```python
def _get_tools_schema(self):
    return [
        {
            "type": "function",
            "function": {
                "name": "wfm_list_visits",
                "description": "List OHS visits with optional filters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "state": {
                            "type": "string",
                            "enum": ["draft", "assigned", "confirmed", ...],
                            "description": "Filter by visit state"
                        },
                        "partner_id": {"type": "integer", ...},
                        "date_from": {"type": "string", ...},
                        ...
                    }
                }
            }
        },
        # ... 35+ more tools
    ]
```

**Tool Categories:**

| Category | Tools | Token Estimate |
|----------|-------|----------------|
| Visit Management | 6 tools | ~500 tokens |
| Partner Management | 3 tools | ~300 tokens |
| Client Management | 2 tools | ~200 tokens |
| WhatsApp | 3 tools | ~300 tokens |
| Workflow Automation | 5 tools | ~400 tokens |
| Churn Analytics | 7 tools | ~600 tokens |
| SEPE Compliance | 4 tools | ~350 tokens |
| Billing | 4 tools | ~350 tokens |
| Referrals | 4 tools | ~350 tokens |
| **Total** | **35+ tools** | **~3000 tokens** |

---

### 3. Conversation History (Variable, max ~2000 tokens)

**Source:** `mail_bot.py:_get_conversation_history()`

Retrieves the last 10 messages from the current chat channel:

```python
MAX_HISTORY_MESSAGES = 10

def _get_conversation_history(self, channel, odoobot):
    history = []

    # Get recent messages from mail.message
    messages = self.env['mail.message'].search([
        ('model', '=', 'discuss.channel'),
        ('res_id', '=', channel.id),
        ('message_type', 'in', ['comment', 'notification']),
    ], order='id desc', limit=MAX_HISTORY_MESSAGES + 1)

    # Skip current message, reverse to chronological order
    messages = list(reversed(messages[1:]))

    for msg in messages:
        role = "assistant" if msg.author_id == odoobot else "user"
        content = self._strip_html(msg.body or "")
        if content.strip():
            history.append({"role": role, "content": content})

    return history
```

**Storage:** Messages are stored in Odoo's `mail.message` table (database), not in memory.

---

### 4. Tool Execution Results (Variable)

**Source:** `llm_client.py:chat_with_tools()`

When tools are called, results are appended to the conversation:

```python
MAX_TOOL_ROUNDS = 5

def chat_with_tools(self, user_message, conversation_history=None):
    messages = [{"role": "system", "content": self._get_system_prompt()}]
    messages.extend(conversation_history or [])
    messages.append({"role": "user", "content": user_message})

    for round_num in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=self._get_model(),
            messages=messages,
            tools=self._get_tools_schema(),
        )

        if response.choices[0].finish_reason == "tool_calls":
            # Execute tools and append results
            for tool_call in response.choices[0].message.tool_calls:
                result = tool_executor.execute_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
        else:
            # Final text response
            return response.choices[0].message.content
```

**Multi-Round Execution:**
- Up to 5 rounds of tool calls per user message
- Each round adds tool results to context
- Context grows during complex queries

---

## Context Token Budget

### Per-Request Token Breakdown

| Component | Tokens | % of Total | Stored? |
|-----------|--------|------------|---------|
| System Prompt | ~400 | 8% | No (regenerated) |
| Tools Schema | ~3000 | 60% | No (regenerated) |
| Conversation History | ~1000-2000 | 20-30% | Yes (mail.message) |
| Current Message | ~50-200 | 2-4% | Yes (mail.message) |
| Tool Results | Variable | Variable | No (in-request only) |
| **Total** | **~5000-8000** | 100% | Partial |

### Comparison with Claude Code

| Aspect | WFM Odoo | Claude Code |
|--------|----------|-------------|
| System Prompt | ~400 tokens | ~3200 tokens |
| Tools | ~3000 tokens (35 tools) | ~127,000 tokens (MCP + built-in) |
| Memory Files | None | ~4000 tokens (CLAUDE.md) |
| Conversation | 10 messages max | Auto-summarization (unlimited) |
| **Total Context** | **~5-8k tokens** | **~200k tokens** |

---

## What Gets Stored vs Regenerated

### Stored (Persistent)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ODOO DATABASE                                 │
├─────────────────────────────────────────────────────────────────┤
│  mail.message                                                    │
│  ├── id: 12345                                                  │
│  ├── model: 'discuss.channel'                                   │
│  ├── res_id: 7 (channel ID)                                     │
│  ├── author_id: 2 (user partner)                                │
│  ├── body: '<p>Show my visits for today</p>'                    │
│  ├── message_type: 'comment'                                    │
│  └── create_date: '2025-12-15 10:30:00'                         │
├─────────────────────────────────────────────────────────────────┤
│  ir.config_parameter                                             │
│  ├── wfm_ai_chat.litellm_api_key: 'sk-xxx'                      │
│  ├── wfm_ai_chat.litellm_base_url: 'https://prod.litellm...'    │
│  └── wfm_ai_chat.model: 'claude-3-5-haiku-latest'               │
└─────────────────────────────────────────────────────────────────┘
```

### Regenerated (Every Request)

```
┌─────────────────────────────────────────────────────────────────┐
│                    IN-MEMORY (Per Request)                       │
├─────────────────────────────────────────────────────────────────┤
│  System Prompt                                                   │
│  ├── User name from self.env.user                               │
│  ├── Current date from self.env.cr.now()                        │
│  └── Static instructions and tool list                          │
├─────────────────────────────────────────────────────────────────┤
│  Tools Schema                                                    │
│  └── 35+ tool definitions (always same)                         │
├─────────────────────────────────────────────────────────────────┤
│  Tool Results                                                    │
│  └── Ephemeral - only exists during request processing          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Role-Based Context

### Context Differences by User Role

| Context Element | WFM Admin | WFM Coordinator | WFM Partner |
|-----------------|-----------|-----------------|-------------|
| System Prompt | Same | Same | Same |
| `user.name` | "Gaurav Sharma" | "Mike Coordinator" | "Panos Andrikopoulos" |
| Tools Available | All 35+ | All 35+ | All 35+ |
| Data Access | All records | All records | **Filtered*** |

*Partner data access is controlled by Odoo record rules, not the AI system.

### How Data Filtering Works

```python
# wfm_tools.py - Tool execution respects Odoo security
def _tool_wfm_list_visits(self, **kwargs):
    domain = []

    # Odoo automatically filters by user's record rules
    # Partner users only see their own visits
    visits = self.env['wfm.visit'].search(domain, limit=limit)

    # self.env uses current user's permissions
    # No additional filtering needed - Odoo handles it
```

---

## Context Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        REQUEST LIFECYCLE                                     │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: User sends message in Odoo Discuss
        ┌─────────────────────────────────────────────┐
        │ User: "Assign Dr. Papadopoulos to visit 5" │
        └─────────────────────────────────────────────┘
                              │
                              ▼
Step 2: mail.bot intercepts (mail_bot.py)
        ┌─────────────────────────────────────────────┐
        │ - Check if direct chat with OdooBot        │
        │ - Check if @OdooBot mentioned              │
        │ - Get conversation history (last 10 msgs)  │
        └─────────────────────────────────────────────┘
                              │
                              ▼
Step 3: Build context (llm_client.py)
        ┌─────────────────────────────────────────────┐
        │ messages = [                                │
        │   {system: "You are AI for GEP..."},       │
        │   {user: "Show visits"},        ◄─ History │
        │   {assistant: "Here are..."},   ◄─ History │
        │   {user: "Assign Dr..."}        ◄─ Current │
        │ ]                                          │
        │ tools = [35 tool definitions]              │
        └─────────────────────────────────────────────┘
                              │
                              ▼
Step 4: LLM API call (LiteLLM Proxy)
        ┌─────────────────────────────────────────────┐
        │ POST https://prod.litellm.deeprunner.ai    │
        │ Model: claude-3-5-haiku-latest             │
        │ Payload: ~5000-8000 tokens                 │
        └─────────────────────────────────────────────┘
                              │
                              ▼
Step 5: Tool call response
        ┌─────────────────────────────────────────────┐
        │ {                                          │
        │   "tool_calls": [{                         │
        │     "function": {                          │
        │       "name": "wfm_assign_partner",        │
        │       "arguments": {                       │
        │         "visit_id": 5,                     │
        │         "partner_id": 12                   │
        │       }                                    │
        │     }                                      │
        │   }]                                       │
        │ }                                          │
        └─────────────────────────────────────────────┘
                              │
                              ▼
Step 6: Execute tool (wfm_tools.py)
        ┌─────────────────────────────────────────────┐
        │ visit = env['wfm.visit'].browse(5)         │
        │ visit.write({'partner_id': 12})            │
        │ return {"success": True, "message": "..."}  │
        └─────────────────────────────────────────────┘
                              │
                              ▼
Step 7: Append result, call LLM again
        ┌─────────────────────────────────────────────┐
        │ messages.append({                          │
        │   "role": "tool",                          │
        │   "content": '{"success": true, ...}'      │
        │ })                                         │
        │ # Second LLM call with tool result         │
        └─────────────────────────────────────────────┘
                              │
                              ▼
Step 8: Final response to user
        ┌─────────────────────────────────────────────┐
        │ "Done! Dr. Papadopoulos has been assigned  │
        │  to visit #5 at Vodafone Athens."          │
        └─────────────────────────────────────────────┘
```

---

## Current Limitations

### 1. No Persistent Memory

**Problem:** The system has no memory across sessions.

```
Session 1 (Monday):
User: "I'm focusing on Athens partners this week"
AI: "Got it, I'll help with Athens partners"

Session 2 (Tuesday):
User: "Show me the partners"
AI: "Which partners? Can you be more specific?"  ← Lost context!
```

**Impact:** Users must repeat context in every conversation.

### 2. Hard Cutoff at 10 Messages

**Problem:** Conversations longer than 10 messages lose early context.

```python
MAX_HISTORY_MESSAGES = 10  # Hard limit

# Message 1-10: In context
# Message 11+: Lost forever
```

**Impact:** Complex multi-step tasks may fail mid-conversation.

### 3. No User Preferences Storage

**Problem:** User preferences aren't remembered.

| Preference Type | Stored? | Example |
|-----------------|---------|---------|
| Date format preference | No | "I prefer DD/MM/YYYY" |
| Default filters | No | "Always show Athens first" |
| Communication style | No | "I like brief responses" |

### 4. No Cross-Channel Context

**Problem:** Each channel has separate history.

```
Channel A (Direct with OdooBot):
- Conversation about visits

Channel B (Group with @OdooBot mention):
- No knowledge of Channel A conversation
```

---

## Recommended Improvements

### 1. Add User AI Context Model

```python
class WfmUserAIContext(models.Model):
    _name = 'wfm.user.ai.context'
    _description = 'User AI Context Storage'

    user_id = fields.Many2one('res.users', required=True, index=True)
    preferences = fields.Text(help="User preferences in JSON")
    recent_topics = fields.Text(help="Recent conversation topics")
    important_facts = fields.Text(help="Key facts to remember")
    conversation_summary = fields.Text(help="Summarized conversation history")
    last_updated = fields.Datetime(default=fields.Datetime.now)
```

### 2. Implement Conversation Summarization

```python
def _summarize_if_needed(self, messages):
    """Summarize conversation when approaching token limit."""
    if len(messages) > 8:  # Approaching limit
        summary_prompt = "Summarize this conversation in 2-3 sentences..."
        summary = self._call_llm(summary_prompt)

        # Store summary
        self._update_user_context(summary=summary)

        # Return condensed history
        return [
            {"role": "system", "content": f"Previous context: {summary}"},
            *messages[-4:]  # Keep last 4 messages
        ]
    return messages
```

### 3. Add Role-Based Tool Filtering

```python
def _get_tools_for_user(self):
    """Return tools based on user role."""
    user = self.env.user
    all_tools = self._get_tools_schema()

    if user.has_group('wfm_portal.group_wfm_partner'):
        # Partners get limited tools
        allowed = ['wfm_list_visits', 'wfm_confirm_visit', ...]
        return [t for t in all_tools if t['function']['name'] in allowed]

    return all_tools  # Admins/Coordinators get all tools
```

### 4. Inject User Context into System Prompt

```python
def _get_system_prompt(self):
    user = self.env.user

    # Get stored context
    context = self.env['wfm.user.ai.context'].search([
        ('user_id', '=', user.id)
    ], limit=1)

    user_memory = ""
    if context:
        user_memory = f"""
## User Memory
- Preferences: {context.preferences}
- Recent topics: {context.recent_topics}
- Important context: {context.important_facts}
- Last conversation summary: {context.conversation_summary}
"""

    return f"""You are an AI assistant...

Current user: {user.name}
Current date: {today}

{user_memory}

Guidelines:
...
"""
```

---

## Token Cost Analysis

### Current Cost per Request

| Component | Input Tokens | Output Tokens |
|-----------|--------------|---------------|
| System Prompt | 400 | - |
| Tools Schema | 3000 | - |
| History (avg) | 1000 | - |
| Current Message | 100 | - |
| Tool Results | 500 | - |
| **Subtotal Input** | **5000** | - |
| LLM Response | - | 200 |
| **Total** | **5000** | **200** |

### Cost Calculation (Claude Haiku)

```
Input: 5000 tokens × $0.25/MTok = $0.00125
Output: 200 tokens × $1.25/MTok = $0.00025
Total per request: ~$0.0015

Daily (100 requests): ~$0.15
Monthly (3000 requests): ~$4.50
```

### With Improvements (Projected)

| Improvement | Token Change | Cost Impact |
|-------------|--------------|-------------|
| User context storage | +200 tokens | +$0.0001 |
| Conversation summary | -500 tokens | -$0.0003 |
| Role-based tools | -1000 tokens (partners) | -$0.0005 |
| **Net Change** | **-300 tokens** | **-$0.0002** |

---

## Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `wfm_ai_chat/models/llm_client.py` | LLM API client, context building | ~1078 |
| `wfm_ai_chat/models/mail_bot.py` | OdooBot integration, history retrieval | ~207 |
| `wfm_ai_chat/tools/wfm_tools.py` | Tool executor, 35+ tools | ~1465 |
| `wfm_fsm/models/ai_retention_engine.py` | AI retention strategy generator | ~574 |

---

## Conclusion

The current WFM AI Chat system uses a **stateless, regenerated context** approach:

- **Pros:** Simple, no storage overhead, always fresh user info
- **Cons:** No memory, limited history, repetitive context for users

To achieve Claude Code-like intelligence, implement:
1. Persistent user context storage (`wfm.user.ai.context`)
2. Conversation summarization for longer sessions
3. Role-based tool filtering for security and efficiency
4. Cross-session memory for user preferences
