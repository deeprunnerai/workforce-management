import json
import logging

from odoo import models, api

_logger = logging.getLogger(__name__)

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    _logger.warning("openai library not installed. AI chat will not work.")


class LLMClient(models.AbstractModel):
    """LLM Client for interacting with LiteLLM proxy."""

    _name = 'wfm.llm.client'
    _description = 'LLM Client for AI Chat'

    def _get_client(self):
        """Get configured OpenAI client pointing to LiteLLM proxy."""
        if not HAS_OPENAI:
            return None

        ICP = self.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('wfm_ai_chat.litellm_api_key', '')
        base_url = ICP.get_param('wfm_ai_chat.litellm_base_url', 'https://prod.litellm.deeprunner.ai')

        if not api_key:
            _logger.warning("LiteLLM API key not configured")
            return None

        return openai.OpenAI(api_key=api_key, base_url=base_url)

    def _get_model(self):
        """Get the configured model name."""
        ICP = self.env['ir.config_parameter'].sudo()
        return ICP.get_param('wfm_ai_chat.model', 'claude-3-5-haiku-latest')

    def _get_system_prompt(self):
        """Get system prompt for the LLM."""
        user = self.env.user
        today = self.env.context.get('today') or str(self.env.cr.now().date())

        return f"""You are an AI assistant for the GEP OHS Workforce Management System.
You help coordinators, admins, and partners manage OHS (Occupational Health & Safety) visits.

Current user: {user.name}
Current date: {today}

You have access to these tools to interact with the WFM system:
- wfm_list_visits: List visits with optional filters (date, state, partner, client)
- wfm_get_visit: Get details of a specific visit by ID or reference
- wfm_list_partners: List OHS partners (physicians, safety engineers)
- wfm_list_clients: List WFM clients
- wfm_assign_partner: Assign a partner to a visit
- wfm_update_visit: Update visit date/time
- wfm_dashboard_stats: Get dashboard statistics
- wfm_send_whatsapp: Send a custom WhatsApp message to a partner
- wfm_send_visit_notification: Send predefined WhatsApp notification (assignment/confirmation/reminder/cancellation)
- wfm_list_whatsapp_messages: List WhatsApp message history
- wfm_create_workflow: Create an autonomous workflow that runs on a schedule
- wfm_list_workflows: List existing workflows
- wfm_update_workflow: Update a workflow's prompt or schedule
- wfm_run_workflow: Manually trigger a workflow now
- wfm_workflow_logs: Get execution logs for a workflow
- wfm_list_at_risk_partners: List partners at risk of churning (high/critical risk)
- wfm_get_partner_health: Get detailed churn risk analysis for a partner
- wfm_log_retention_action: Log a retention intervention (call, email, meeting, etc.)
- wfm_resolve_retention_ticket: Resolve a retention ticket with outcome
- wfm_churn_dashboard_stats: Get churn analysis dashboard statistics
- wfm_get_ai_retention_strategy: Get AI-powered retention strategy for a partner
- wfm_run_churn_computation: Trigger churn risk computation for all partners
- wfm_list_sepe_exports: List SEPE export batches
- wfm_create_sepe_export: Create a new SEPE export for a date range
- wfm_get_sepe_export: Get details of a specific SEPE export
- wfm_submit_sepe_export: Mark SEPE export as submitted to government
- wfm_billing_stats: Get billing dashboard statistics
- wfm_update_billing_status: Update billing status of visits
- wfm_list_unbilled_visits: List visits pending billing
- wfm_list_referrals: List partner referrals
- wfm_get_referral: Get details of a specific referral
- wfm_update_referral: Update referral status (start_review, accept, reject)
- wfm_referral_stats: Get referral program statistics

Guidelines:
1. Always be helpful and concise
2. When listing data, format it clearly
3. Confirm actions before making changes
4. If unsure, ask clarifying questions
5. Use Greek names for partners and clients when displaying
6. Format dates in DD/MM/YYYY format for Greek users

When responding:
- Keep responses concise (chat messages should be short)
- Use bullet points for lists
- Don't include code or technical details unless asked
"""

    def _get_tools_schema(self):
        """Get tool definitions for function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "wfm_list_visits",
                    "description": "List OHS visits with optional filters. Returns visit ID, reference, client, installation, partner, date, and state.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {
                                "type": "string",
                                "enum": ["draft", "assigned", "confirmed", "in_progress", "done", "cancelled"],
                                "description": "Filter by visit state"
                            },
                            "partner_id": {
                                "type": "integer",
                                "description": "Filter by partner ID"
                            },
                            "client_id": {
                                "type": "integer",
                                "description": "Filter by client ID"
                            },
                            "date_from": {
                                "type": "string",
                                "description": "Filter visits from this date (YYYY-MM-DD)"
                            },
                            "date_to": {
                                "type": "string",
                                "description": "Filter visits until this date (YYYY-MM-DD)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of visits to return (default 10)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_get_visit",
                    "description": "Get detailed information about a specific visit by ID or reference number",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "visit_id": {
                                "type": "integer",
                                "description": "Visit ID"
                            },
                            "reference": {
                                "type": "string",
                                "description": "Visit reference (e.g., VISIT/0001)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_list_partners",
                    "description": "List OHS partners (physicians, safety engineers) with optional filters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "specialty": {
                                "type": "string",
                                "enum": ["physician", "safety_engineer", "health_scientist"],
                                "description": "Filter by partner specialty"
                            },
                            "city": {
                                "type": "string",
                                "description": "Filter by city name"
                            },
                            "available_on": {
                                "type": "string",
                                "description": "Check availability on this date (YYYY-MM-DD)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of partners to return (default 10)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_list_clients",
                    "description": "List WFM clients (companies purchasing OHS services)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search": {
                                "type": "string",
                                "description": "Search term for client name"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of clients to return (default 10)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_assign_partner",
                    "description": "Assign a partner to a visit. This will trigger notifications.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "visit_id": {
                                "type": "integer",
                                "description": "Visit ID to assign"
                            },
                            "partner_id": {
                                "type": "integer",
                                "description": "Partner ID to assign"
                            }
                        },
                        "required": ["visit_id", "partner_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_update_visit",
                    "description": "Update visit details like date, time, or notes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "visit_id": {
                                "type": "integer",
                                "description": "Visit ID to update"
                            },
                            "visit_date": {
                                "type": "string",
                                "description": "New visit date (YYYY-MM-DD)"
                            },
                            "start_time": {
                                "type": "number",
                                "description": "New start time (e.g., 9.5 for 9:30)"
                            },
                            "end_time": {
                                "type": "number",
                                "description": "New end time (e.g., 17.5 for 17:30)"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Visit notes"
                            }
                        },
                        "required": ["visit_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_dashboard_stats",
                    "description": "Get dashboard statistics: visit counts by state, pending assignments, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            # WhatsApp Tools
            {
                "type": "function",
                "function": {
                    "name": "wfm_send_whatsapp",
                    "description": "Send a custom WhatsApp message to a partner. Use this to send direct messages.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "partner_id": {
                                "type": "integer",
                                "description": "Partner ID to send the message to"
                            },
                            "message": {
                                "type": "string",
                                "description": "Message text to send via WhatsApp"
                            },
                            "visit_id": {
                                "type": "integer",
                                "description": "Optional visit ID to link the message to"
                            }
                        },
                        "required": ["partner_id", "message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_send_visit_notification",
                    "description": "Send a predefined WhatsApp notification for a visit (assignment, confirmation, reminder, or cancellation)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "visit_id": {
                                "type": "integer",
                                "description": "Visit ID to send notification for"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["assignment", "confirmed", "reminder", "cancelled"],
                                "description": "Type of notification to send"
                            }
                        },
                        "required": ["visit_id", "type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_list_whatsapp_messages",
                    "description": "List WhatsApp message history with optional filters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "visit_id": {
                                "type": "integer",
                                "description": "Filter by visit ID"
                            },
                            "partner_id": {
                                "type": "integer",
                                "description": "Filter by partner ID"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["pending", "sent", "delivered", "read", "failed"],
                                "description": "Filter by message status"
                            },
                            "message_type": {
                                "type": "string",
                                "enum": ["assignment", "confirmed", "reminder", "cancelled", "custom"],
                                "description": "Filter by message type"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of messages to return (default 10)"
                            }
                        }
                    }
                }
            },
            # Workflow Tools
            {
                "type": "function",
                "function": {
                    "name": "wfm_create_workflow",
                    "description": "Create an autonomous workflow that runs on a schedule. Workflows execute AI agents to perform automated tasks.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the workflow"
                            },
                            "prompt": {
                                "type": "string",
                                "description": "Natural language instructions for the AI agent to execute"
                            },
                            "description": {
                                "type": "string",
                                "description": "Brief description of what the workflow does"
                            },
                            "schedule_type": {
                                "type": "string",
                                "enum": ["manual", "interval", "cron"],
                                "description": "How the workflow is scheduled: manual (run on demand), interval (every X minutes/hours/days), cron (cron expression)"
                            },
                            "interval_number": {
                                "type": "integer",
                                "description": "For interval schedules: how many units between runs"
                            },
                            "interval_type": {
                                "type": "string",
                                "enum": ["minutes", "hours", "days", "weeks"],
                                "description": "For interval schedules: the time unit"
                            },
                            "cron_expression": {
                                "type": "string",
                                "description": "For cron schedules: cron expression (e.g., '0 9 * * *' for daily at 9AM)"
                            }
                        },
                        "required": ["name", "prompt"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_list_workflows",
                    "description": "List existing autonomous workflows",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {
                                "type": "string",
                                "enum": ["draft", "active", "paused", "error"],
                                "description": "Filter by workflow state"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of workflows to return (default 10)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_update_workflow",
                    "description": "Update an existing workflow's configuration",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "integer",
                                "description": "Workflow ID to update"
                            },
                            "name": {
                                "type": "string",
                                "description": "New name for the workflow"
                            },
                            "prompt": {
                                "type": "string",
                                "description": "New prompt/instructions for the AI agent"
                            },
                            "state": {
                                "type": "string",
                                "enum": ["active", "paused"],
                                "description": "Activate or pause the workflow"
                            },
                            "schedule_type": {
                                "type": "string",
                                "enum": ["manual", "interval", "cron"],
                                "description": "New schedule type"
                            },
                            "interval_number": {
                                "type": "integer",
                                "description": "New interval number"
                            },
                            "interval_type": {
                                "type": "string",
                                "enum": ["minutes", "hours", "days", "weeks"],
                                "description": "New interval type"
                            },
                            "cron_expression": {
                                "type": "string",
                                "description": "New cron expression"
                            }
                        },
                        "required": ["workflow_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_run_workflow",
                    "description": "Manually trigger a workflow to run now",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "integer",
                                "description": "Workflow ID to run"
                            }
                        },
                        "required": ["workflow_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_workflow_logs",
                    "description": "Get execution logs for a workflow",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "integer",
                                "description": "Workflow ID to get logs for"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["running", "success", "failed", "timeout", "cancelled"],
                                "description": "Filter by execution status"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of logs to return (default 10)"
                            }
                        }
                    }
                }
            },
            # Churn Analysis Tools
            {
                "type": "function",
                "function": {
                    "name": "wfm_list_at_risk_partners",
                    "description": "List partners at risk of churning. By default shows high and critical risk partners.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "risk_level": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"],
                                "description": "Filter by specific risk level"
                            },
                            "ticket_state": {
                                "type": "string",
                                "enum": ["open", "in_progress", "resolved", "closed"],
                                "description": "Filter by retention ticket state"
                            },
                            "my_tickets": {
                                "type": "boolean",
                                "description": "Only show tickets assigned to current user"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of partners to return (default 20)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_get_partner_health",
                    "description": "Get detailed churn risk analysis for a specific partner, including score breakdown",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "partner_id": {
                                "type": "integer",
                                "description": "Partner ID to get health data for"
                            },
                            "health_id": {
                                "type": "integer",
                                "description": "Health record ID (alternative to partner_id)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_log_retention_action",
                    "description": "Log a retention intervention/action for a partner (call, email, meeting, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "health_id": {
                                "type": "integer",
                                "description": "Health record ID for the partner"
                            },
                            "intervention_type": {
                                "type": "string",
                                "enum": ["call", "whatsapp", "email", "meeting", "bonus", "workload"],
                                "description": "Type of intervention performed"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Notes about the intervention"
                            },
                            "outcome": {
                                "type": "string",
                                "enum": ["positive", "neutral", "negative", "pending"],
                                "description": "Outcome of the intervention"
                            }
                        },
                        "required": ["health_id", "intervention_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_resolve_retention_ticket",
                    "description": "Resolve a retention ticket with outcome (retained, churned, or false alarm)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "health_id": {
                                "type": "integer",
                                "description": "Health record ID to resolve"
                            },
                            "outcome": {
                                "type": "string",
                                "enum": ["retained", "churned", "false_alarm"],
                                "description": "Resolution outcome"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Resolution notes"
                            }
                        },
                        "required": ["health_id", "outcome"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_churn_dashboard_stats",
                    "description": "Get churn analysis dashboard statistics: risk distribution, ticket counts, retention rate",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_get_ai_retention_strategy",
                    "description": "Get AI-powered retention strategy and personalized WhatsApp message for a partner",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "health_id": {
                                "type": "integer",
                                "description": "Health record ID to generate strategy for"
                            }
                        },
                        "required": ["health_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_run_churn_computation",
                    "description": "Trigger churn risk computation for all partners. Updates health records with new risk scores.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            # SEPE Export Tools
            {
                "type": "function",
                "function": {
                    "name": "wfm_list_sepe_exports",
                    "description": "List SEPE export batches with optional filters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {
                                "type": "string",
                                "enum": ["draft", "exported", "submitted"],
                                "description": "Filter by export state"
                            },
                            "date_from": {
                                "type": "string",
                                "description": "Filter exports from this date (YYYY-MM-DD)"
                            },
                            "date_to": {
                                "type": "string",
                                "description": "Filter exports until this date (YYYY-MM-DD)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of exports to return (default 10)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_create_sepe_export",
                    "description": "Create a new SEPE export batch for completed visits in a date range. Automatically generates Excel file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_from": {
                                "type": "string",
                                "description": "Start date for visits to include (YYYY-MM-DD)"
                            },
                            "date_to": {
                                "type": "string",
                                "description": "End date for visits to include (YYYY-MM-DD)"
                            },
                            "include_exported": {
                                "type": "boolean",
                                "description": "Include visits that were already exported (default false)"
                            },
                            "generate_excel": {
                                "type": "boolean",
                                "description": "Generate Excel file immediately (default true)"
                            }
                        },
                        "required": ["date_from", "date_to"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_get_sepe_export",
                    "description": "Get detailed information about a specific SEPE export",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "export_id": {
                                "type": "integer",
                                "description": "SEPE export ID"
                            },
                            "name": {
                                "type": "string",
                                "description": "SEPE export reference (e.g., SEPE/2025/0001)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_submit_sepe_export",
                    "description": "Mark a SEPE export as submitted to the government. Updates visit billing status to 'invoiced'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "export_id": {
                                "type": "integer",
                                "description": "SEPE export ID to mark as submitted"
                            }
                        },
                        "required": ["export_id"]
                    }
                }
            },
            # Billing Tools
            {
                "type": "function",
                "function": {
                    "name": "wfm_billing_stats",
                    "description": "Get billing dashboard statistics: visits by billing status, amounts, and SEPE export counts",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_update_billing_status",
                    "description": "Update billing status of one or more visits",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "visit_id": {
                                "type": "integer",
                                "description": "Single visit ID to update"
                            },
                            "visit_ids": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "Multiple visit IDs to update"
                            },
                            "billing_status": {
                                "type": "string",
                                "enum": ["not_billed", "invoiced", "client_paid", "settled"],
                                "description": "New billing status"
                            },
                            "invoice_reference": {
                                "type": "string",
                                "description": "Optional invoice reference number"
                            }
                        },
                        "required": ["billing_status"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_list_unbilled_visits",
                    "description": "List completed visits that haven't been billed yet",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_id": {
                                "type": "integer",
                                "description": "Filter by client ID"
                            },
                            "partner_id": {
                                "type": "integer",
                                "description": "Filter by partner ID"
                            },
                            "date_from": {
                                "type": "string",
                                "description": "Filter visits from this date (YYYY-MM-DD)"
                            },
                            "date_to": {
                                "type": "string",
                                "description": "Filter visits until this date (YYYY-MM-DD)"
                            },
                            "not_exported": {
                                "type": "boolean",
                                "description": "Only show visits not yet exported to SEPE"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of visits to return (default 20)"
                            }
                        }
                    }
                }
            },
            # Partner Referral Tools
            {
                "type": "function",
                "function": {
                    "name": "wfm_list_referrals",
                    "description": "List partner referrals with optional filters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {
                                "type": "string",
                                "enum": ["draft", "submitted", "under_review", "accepted", "rejected", "meeting_scheduled"],
                                "description": "Filter by referral state"
                            },
                            "referring_partner_id": {
                                "type": "integer",
                                "description": "Filter by referring partner ID"
                            },
                            "coordinator_id": {
                                "type": "integer",
                                "description": "Filter by assigned coordinator ID"
                            },
                            "specialty": {
                                "type": "string",
                                "enum": ["physician", "safety_engineer", "health_scientist", "other"],
                                "description": "Filter by candidate specialty"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of referrals to return (default 10)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_get_referral",
                    "description": "Get detailed information about a specific referral including candidate details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "referral_id": {
                                "type": "integer",
                                "description": "Referral ID"
                            },
                            "reference": {
                                "type": "string",
                                "description": "Referral reference number"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_update_referral",
                    "description": "Update referral status or details. Actions: start_review, accept (requires meeting_date), reject",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "referral_id": {
                                "type": "integer",
                                "description": "Referral ID to update"
                            },
                            "action": {
                                "type": "string",
                                "enum": ["start_review", "accept", "reject"],
                                "description": "Action to perform on the referral"
                            },
                            "meeting_date": {
                                "type": "string",
                                "description": "Meeting date for acceptance (YYYY-MM-DD HH:MM:SS)"
                            },
                            "meeting_location": {
                                "type": "string",
                                "description": "Meeting location or video link"
                            },
                            "rejection_reason": {
                                "type": "string",
                                "description": "Reason for rejection"
                            },
                            "review_notes": {
                                "type": "string",
                                "description": "Internal coordinator notes"
                            }
                        },
                        "required": ["referral_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wfm_referral_stats",
                    "description": "Get referral program statistics: counts by state, specialty, and top referrers",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]

    def chat(self, message, conversation_history=None):
        """
        Send a message to the LLM and get a response.

        Args:
            message: User message
            conversation_history: List of previous messages (optional)

        Returns:
            dict with 'response' (text) and 'tool_calls' (if any)
        """
        client = self._get_client()
        if not client:
            return {
                'response': "AI chat is not configured. Please contact your administrator.",
                'tool_calls': []
            }

        messages = [{"role": "system", "content": self._get_system_prompt()}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": message})

        try:
            response = client.chat.completions.create(
                model=self._get_model(),
                messages=messages,
                tools=self._get_tools_schema(),
                tool_choice="auto",
                max_tokens=1024,
            )

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                return {
                    'response': None,
                    'tool_calls': [
                        {
                            'id': tc.id,
                            'name': tc.function.name,
                            'arguments': json.loads(tc.function.arguments)
                        }
                        for tc in choice.message.tool_calls
                    ],
                    'message': choice.message
                }
            else:
                return {
                    'response': choice.message.content or "",
                    'tool_calls': []
                }

        except Exception as e:
            _logger.error(f"LLM API error: {e}")
            return {
                'response': f"Sorry, I encountered an error: {str(e)}",
                'tool_calls': []
            }

    def chat_with_tools(self, message, conversation_history=None, max_rounds=5):
        """
        Complete chat interaction with automatic tool execution.

        Supports multiple rounds of tool calls (up to max_rounds).
        Returns the final text response after executing all tool calls.
        """
        tool_executor = self.env['wfm.tool.executor']
        client = self._get_client()

        if not client:
            return "AI chat is not configured. Please contact your administrator."

        # Build initial messages
        messages = [{"role": "system", "content": self._get_system_prompt()}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": message})

        # Allow multiple rounds of tool calls
        for round_num in range(max_rounds):
            try:
                response = client.chat.completions.create(
                    model=self._get_model(),
                    messages=messages,
                    tools=self._get_tools_schema(),
                    tool_choice="auto",
                    max_tokens=2048,
                )

                choice = response.choices[0]

                # If no tool calls, return the text response
                if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
                    return choice.message.content or "Done."

                # Add assistant's message with tool calls
                messages.append(choice.message)

                # Execute all tool calls
                for tool_call in choice.message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        tool_result = tool_executor.execute(tool_name, arguments)
                        _logger.info(f"Tool {tool_name} executed successfully")
                    except Exception as e:
                        _logger.error(f"Tool execution error for {tool_name}: {e}")
                        tool_result = {"error": str(e)}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })

            except Exception as e:
                _logger.error(f"LLM API error in round {round_num}: {e}")
                return f"Sorry, I encountered an error: {str(e)}"

        # If we've exhausted all rounds, force a final text response
        try:
            response = client.chat.completions.create(
                model=self._get_model(),
                messages=messages,
                tools=self._get_tools_schema(),
                tool_choice="none",  # Force text response
                max_tokens=2048,
            )
            return response.choices[0].message.content or "Done."
        except Exception as e:
            _logger.error(f"LLM API error in final response: {e}")
            return "I've completed the requested actions."
