# WFM Notification Workflow

## Overview

The WFM system uses a dual notification approach:
1. **Automatic Notifications** - Triggered by workflow events
2. **Manual Notifications** - Sent by coordinators via Odoo chatter

Both types are delivered via **WhatsApp** (Twilio) and logged in-app.

---

## Notification Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ODOO WFM SYSTEM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │ Visit State │───▶│ Notification│───▶│ wfm_whatsapp module │ │
│  │   Change    │    │   Trigger   │    │                     │ │
│  └─────────────┘    └─────────────┘    │  ┌───────────────┐  │ │
│                                        │  │ Twilio API    │  │ │
│  ┌─────────────┐    ┌─────────────┐    │  │ (WhatsApp)    │  │ │
│  │ Coordinator │───▶│ Odoo Chatter│───▶│  └───────┬───────┘  │ │
│  │   Message   │    │  Message    │    │          │          │ │
│  └─────────────┘    └─────────────┘    │  ┌───────▼───────┐  │ │
│                                        │  │ Message Log   │  │ │
│  ┌─────────────┐                       │  │ (wfm.whatsapp │  │ │
│  │  Scheduled  │───────────────────────│  │   .message)   │  │ │
│  │   Actions   │                       │  └───────────────┘  │ │
│  └─────────────┘                       └─────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Partner Phone  │
                    │   (WhatsApp)    │
                    └─────────────────┘
```

---

## Automatic Notifications (Autonomous Agent)

### Trigger Events

| Event | Trigger | Message Template |
|-------|---------|------------------|
| **Partner Assigned** | `partner_id` set on visit | Assignment notification |
| **Visit Confirmed** | State → `confirmed` | Confirmation acknowledgment |
| **24h Reminder** | Scheduled action | Reminder with visit details |
| **Visit Cancelled** | State → `cancelled` | Cancellation notice |

### Implementation

```python
# In wfm.visit model
def write(self, vals):
    result = super().write(vals)

    # Trigger on partner assignment
    if 'partner_id' in vals and vals['partner_id']:
        self._send_whatsapp_notification('assignment')

    # Trigger on state changes
    if 'state' in vals:
        if vals['state'] == 'confirmed':
            self._send_whatsapp_notification('confirmed')
        elif vals['state'] == 'cancelled':
            self._send_whatsapp_notification('cancelled')

    return result
```

---

## Manual Notifications (Coordinator → Partner)

### How It Works

1. Coordinator opens a visit form
2. Clicks "Send WhatsApp" button or uses chatter
3. Types message in popup/chatter
4. System sends via Twilio WhatsApp API
5. Message logged in visit chatter + `wfm.whatsapp.message`

### Integration with Odoo Chatter

Option A: **Dedicated WhatsApp Button**
- New button "Send WhatsApp" on visit form
- Opens wizard to compose message
- Sends to partner's phone via Twilio

Option B: **Chatter Integration** (Advanced)
- Special syntax in chatter: `@whatsapp: Your message here`
- System detects and routes to WhatsApp
- Regular messages stay as internal notes

**Recommended: Option A** (simpler, clearer UX)

---

## Message Templates

### 1. Assignment Notification
```
🏥 GEP OHS - New Visit Assignment

Hello {partner_name},

You have been assigned to a new visit:

📅 Date: {visit_date}
⏰ Time: {start_time} - {end_time}
🏢 Client: {client_name}
📍 Location: {installation_name}
   {installation_address}

Please confirm your availability in the Partner Portal:
{portal_url}

Questions? Contact your coordinator.
```

### 2. Confirmation Acknowledgment
```
✅ Visit Confirmed

Your visit on {visit_date} at {client_name} has been confirmed.

📍 {installation_address}
⏰ {start_time} - {end_time}

See you there!
```

### 3. 24-Hour Reminder
```
⏰ Reminder: Visit Tomorrow

Hello {partner_name},

Reminder of your scheduled visit:

📅 Tomorrow, {visit_date}
⏰ {start_time}
🏢 {client_name}
📍 {installation_address}

Safe travels!
```

### 4. Cancellation Notice
```
❌ Visit Cancelled

The following visit has been cancelled:

📅 {visit_date}
🏢 {client_name}

Please check the Portal for updated schedule.
```

### 5. Custom Message (Coordinator)
```
📨 Message from GEP Coordinator

{custom_message}

---
Re: Visit {visit_reference}
{visit_date} at {client_name}
```

---

## Data Model

### wfm.whatsapp.message

| Field | Type | Description |
|-------|------|-------------|
| `visit_id` | Many2one | Related visit |
| `partner_id` | Many2one | Recipient partner |
| `phone` | Char | WhatsApp number |
| `message_type` | Selection | assignment/confirmed/reminder/cancelled/custom |
| `message_body` | Text | Full message content |
| `status` | Selection | pending/sent/delivered/failed |
| `twilio_sid` | Char | Twilio message SID |
| `sent_at` | Datetime | Send timestamp |
| `error_message` | Text | Error details if failed |

---

## Scheduled Actions

### 24-Hour Reminder Cron

```xml
<record id="ir_cron_whatsapp_reminder" model="ir.cron">
    <field name="name">WhatsApp: 24h Visit Reminder</field>
    <field name="model_id" ref="wfm_core.model_wfm_visit"/>
    <field name="state">code</field>
    <field name="code">model._send_24h_reminders()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">hours</field>
    <field name="numbercall">-1</field>
    <field name="active">True</field>
</record>
```

---

## Security Considerations

1. **Phone Number Validation** - Ensure valid WhatsApp format (+countrycode)
2. **Rate Limiting** - Max 100 messages/hour to avoid Twilio blocks
3. **Opt-out Handling** - Respect partner preferences
4. **Message Logging** - Full audit trail in database
5. **Credentials** - Store in environment variables, not code

---

## User Interface

### Visit Form - WhatsApp Button

```xml
<button name="action_send_whatsapp"
        string="Send WhatsApp"
        type="object"
        class="btn-success"
        icon="fa-whatsapp"
        invisible="not partner_id"/>
```

### WhatsApp Message Wizard

- Partner info (readonly)
- Message template dropdown
- Custom message textarea
- Preview before send
- Send button

### Message Log Tab on Visit

```xml
<page string="WhatsApp Messages" name="whatsapp_messages">
    <field name="whatsapp_message_ids" readonly="1">
        <list>
            <field name="sent_at"/>
            <field name="message_type"/>
            <field name="status" widget="badge"/>
        </list>
    </field>
</page>
```

---

## Configuration

### Twilio Webhook URLs

Configure these URLs in your Twilio WhatsApp Sandbox or Business settings:

| Setting | URL |
|---------|-----|
| **Webhook URL (incoming messages)** | `https://odoo.deeprunner.ai/whatsapp/webhook` |
| **Status Callback URL** | `https://odoo.deeprunner.ai/whatsapp/status` |

### Environment Variables

Set these in the Docker container or server environment:

```bash
TWILIO_ACCOUNT_SID=<your_account_sid>
TWILIO_AUTH_TOKEN=<your_auth_token>
TWILIO_WHATSAPP_NUMBER=+14155238886
```

### Odoo System Parameters

| Key | Value | Description |
|-----|-------|-------------|
| `wfm.whatsapp.enabled` | True/False | Enable/disable WhatsApp |
| `wfm.whatsapp.reminder_hours` | 24 | Hours before visit for reminder |

---

## Partner Commands (WhatsApp)

Partners can reply to WhatsApp messages with these commands:

### Basic Commands

| Command | Variations | Action |
|---------|------------|--------|
| **ACCEPT** | YES, OK, CONFIRM | Confirm latest assigned visit |
| **DENY** | NO, CANCEL, REJECT | Decline latest assigned visit |
| **help** | ? | Show help information |
| **visits** | UPCOMING | List upcoming visits |
| **status** | - | Check current assignment |

### Visit-Specific Commands

| Command | Example | Action |
|---------|---------|--------|
| **visit N** | `visit 1` | Show details for visit #N with Google Maps link |
| **visit N accept** | `visit 1 accept` | Confirm specific visit #N |
| **visit N deny** | `visit 2 deny` | Decline specific visit #N |

### Example Flow

1. Partner sends `visits` → sees numbered list of upcoming visits
2. Partner sends `visit 1` → sees full details with map link
3. Partner sends `visit 1 accept` → confirms that specific visit

### Validation Rules

- Cannot deny an already confirmed visit (must contact coordinator)
- Cannot accept an already confirmed visit (shows info message)
- Visit numbers match the order shown in `visits` list

---

## Testing Checklist

### Outgoing Messages
- [x] Assignment triggers WhatsApp
- [ ] Confirmation triggers WhatsApp
- [ ] Manual "Send WhatsApp" works
- [x] Message logged in database
- [ ] 24h reminder cron fires correctly

### Incoming Commands
- [x] `help` returns command list
- [x] `visits` returns upcoming visits
- [x] `visit 1` returns visit details with Google Maps
- [x] `visit 1 accept` confirms specific visit
- [x] `visit 1 deny` declines specific visit
- [x] `ACCEPT` confirms latest assigned visit
- [x] `DENY` declines latest assigned visit
- [x] `status` shows current assignment

### Error Handling
- [x] Unknown partner shows error message
- [x] Invalid visit number shows error
- [x] Already confirmed visit cannot be denied

---

**Document Version:** 1.1
**Last Updated:** 2025-12-13
