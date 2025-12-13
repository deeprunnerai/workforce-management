import logging
from datetime import datetime, timedelta

from odoo import models, api, fields

_logger = logging.getLogger(__name__)


class WfmToolExecutor(models.AbstractModel):
    """Executes WFM tools called by the LLM."""

    _name = 'wfm.tool.executor'
    _description = 'WFM Tool Executor'

    def execute(self, tool_name, arguments):
        """Execute a tool by name with given arguments."""
        method_name = f'_tool_{tool_name}'
        if hasattr(self, method_name):
            return getattr(self, method_name)(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _tool_wfm_list_visits(self, args):
        """List visits with optional filters."""
        Visit = self.env['wfm.visit']
        domain = []

        if args.get('state'):
            domain.append(('state', '=', args['state']))

        if args.get('partner_id'):
            domain.append(('partner_id', '=', args['partner_id']))

        if args.get('client_id'):
            domain.append(('client_id', '=', args['client_id']))

        if args.get('date_from'):
            domain.append(('visit_date', '>=', args['date_from']))

        if args.get('date_to'):
            domain.append(('visit_date', '<=', args['date_to']))

        limit = args.get('limit', 10)

        visits = Visit.search(domain, limit=limit, order='visit_date desc')

        result = []
        for v in visits:
            result.append({
                'id': v.id,
                'reference': v.name,
                'client': v.client_id.name,
                'installation': v.installation_id.name,
                'address': v.installation_id.address or '',
                'partner': v.partner_id.name if v.partner_id else 'Not assigned',
                'date': v.visit_date.strftime('%d/%m/%Y') if v.visit_date else '',
                'time': f"{int(v.start_time)}:{int((v.start_time % 1) * 60):02d}" if v.start_time else '',
                'state': v.state,
                'state_label': dict(Visit._fields['state'].selection).get(v.state, v.state),
            })

        return {
            'count': len(result),
            'visits': result
        }

    def _tool_wfm_get_visit(self, args):
        """Get details of a specific visit."""
        Visit = self.env['wfm.visit']

        visit = None
        if args.get('visit_id'):
            visit = Visit.browse(args['visit_id'])
        elif args.get('reference'):
            visit = Visit.search([('name', '=', args['reference'])], limit=1)

        if not visit or not visit.exists():
            return {'error': 'Visit not found'}

        return {
            'id': visit.id,
            'reference': visit.name,
            'client': {
                'id': visit.client_id.id,
                'name': visit.client_id.name,
            },
            'installation': {
                'id': visit.installation_id.id,
                'name': visit.installation_id.name,
                'address': visit.installation_id.address or '',
                'city': visit.installation_id.city or '',
            },
            'partner': {
                'id': visit.partner_id.id,
                'name': visit.partner_id.name,
                'specialty': visit.partner_id.specialty,
                'phone': visit.partner_id.phone or '',
            } if visit.partner_id else None,
            'date': visit.visit_date.strftime('%d/%m/%Y') if visit.visit_date else '',
            'start_time': f"{int(visit.start_time)}:{int((visit.start_time % 1) * 60):02d}",
            'end_time': f"{int(visit.end_time)}:{int((visit.end_time % 1) * 60):02d}",
            'duration': f"{visit.duration:.1f} hours",
            'state': visit.state,
            'state_label': dict(Visit._fields['state'].selection).get(visit.state, visit.state),
            'visit_type': visit.visit_type,
            'notes': visit.notes or '',
        }

    def _tool_wfm_list_partners(self, args):
        """List OHS partners with optional filters."""
        Partner = self.env['res.partner']
        domain = [('is_wfm_partner', '=', True)]

        if args.get('specialty'):
            domain.append(('specialty', '=', args['specialty']))

        if args.get('city'):
            domain.append(('city', 'ilike', args['city']))

        limit = args.get('limit', 10)
        partners = Partner.search(domain, limit=limit)

        result = []
        for p in partners:
            partner_data = {
                'id': p.id,
                'name': p.name,
                'specialty': p.specialty,
                'specialty_label': dict(Partner._fields['specialty'].selection).get(p.specialty, p.specialty) if p.specialty else '',
                'city': p.city or '',
                'phone': p.phone or '',
                'email': p.email or '',
                'hourly_rate': p.hourly_rate,
            }

            # Check availability if requested
            if args.get('available_on'):
                check_date = args['available_on']
                visit_count = self.env['wfm.visit'].search_count([
                    ('partner_id', '=', p.id),
                    ('visit_date', '=', check_date),
                    ('state', 'not in', ['cancelled', 'done']),
                ])
                partner_data['visits_on_date'] = visit_count
                partner_data['available'] = visit_count < 3  # Assume max 3 visits/day

            result.append(partner_data)

        return {
            'count': len(result),
            'partners': result
        }

    def _tool_wfm_list_clients(self, args):
        """List WFM clients."""
        Partner = self.env['res.partner']
        domain = [('is_wfm_client', '=', True)]

        if args.get('search'):
            domain.append(('name', 'ilike', args['search']))

        limit = args.get('limit', 10)
        clients = Partner.search(domain, limit=limit)

        result = []
        for c in clients:
            result.append({
                'id': c.id,
                'name': c.name,
                'city': c.city or '',
                'phone': c.phone or '',
                'email': c.email or '',
                'installation_count': c.installation_count,
            })

        return {
            'count': len(result),
            'clients': result
        }

    def _tool_wfm_assign_partner(self, args):
        """Assign a partner to a visit."""
        if not args.get('visit_id') or not args.get('partner_id'):
            return {'error': 'Both visit_id and partner_id are required'}

        Visit = self.env['wfm.visit']
        Partner = self.env['res.partner']

        visit = Visit.browse(args['visit_id'])
        if not visit.exists():
            return {'error': f"Visit {args['visit_id']} not found"}

        partner = Partner.browse(args['partner_id'])
        if not partner.exists() or not partner.is_wfm_partner:
            return {'error': f"Partner {args['partner_id']} not found or not a WFM partner"}

        # Check if visit already has this partner
        if visit.partner_id.id == partner.id:
            return {
                'success': True,
                'message': f"Partner {partner.name} was already assigned to {visit.name}",
                'visit_reference': visit.name,
            }

        # Assign the partner (this triggers notification via write override)
        visit.write({
            'partner_id': partner.id,
            'state': 'assigned' if visit.state == 'draft' else visit.state,
        })

        return {
            'success': True,
            'message': f"Assigned {partner.name} to visit {visit.name} at {visit.installation_id.name}",
            'visit_reference': visit.name,
            'partner_name': partner.name,
            'visit_date': visit.visit_date.strftime('%d/%m/%Y'),
        }

    def _tool_wfm_update_visit(self, args):
        """Update visit details."""
        if not args.get('visit_id'):
            return {'error': 'visit_id is required'}

        Visit = self.env['wfm.visit']
        visit = Visit.browse(args['visit_id'])

        if not visit.exists():
            return {'error': f"Visit {args['visit_id']} not found"}

        vals = {}
        if args.get('visit_date'):
            vals['visit_date'] = args['visit_date']
        if args.get('start_time') is not None:
            vals['start_time'] = args['start_time']
        if args.get('end_time') is not None:
            vals['end_time'] = args['end_time']
        if args.get('notes') is not None:
            vals['notes'] = args['notes']

        if not vals:
            return {'error': 'No fields to update provided'}

        visit.write(vals)

        return {
            'success': True,
            'message': f"Updated visit {visit.name}",
            'updated_fields': list(vals.keys()),
            'visit_reference': visit.name,
        }

    def _tool_wfm_dashboard_stats(self, args):
        """Get dashboard statistics."""
        Visit = self.env['wfm.visit']
        Partner = self.env['res.partner']
        today = fields.Date.today()

        # Visit counts by state
        states = ['draft', 'assigned', 'confirmed', 'in_progress', 'done', 'cancelled']
        state_counts = {}
        for state in states:
            state_counts[state] = Visit.search_count([('state', '=', state)])

        # Pending assignments (draft visits)
        pending = Visit.search_count([('state', '=', 'draft')])

        # Today's visits
        today_visits = Visit.search_count([('visit_date', '=', today)])
        today_completed = Visit.search_count([
            ('visit_date', '=', today),
            ('state', '=', 'done')
        ])

        # This week
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        this_week_visits = Visit.search_count([
            ('visit_date', '>=', week_start),
            ('visit_date', '<=', week_end),
        ])

        # Partner counts
        total_partners = Partner.search_count([('is_wfm_partner', '=', True)])
        physicians = Partner.search_count([
            ('is_wfm_partner', '=', True),
            ('specialty', '=', 'physician')
        ])
        engineers = Partner.search_count([
            ('is_wfm_partner', '=', True),
            ('specialty', '=', 'safety_engineer')
        ])

        # Overdue visits (past date, not completed)
        overdue = Visit.search_count([
            ('visit_date', '<', today),
            ('state', 'not in', ['done', 'cancelled']),
        ])

        return {
            'summary': {
                'total_visits': sum(state_counts.values()) - state_counts.get('cancelled', 0),
                'pending_assignments': pending,
                'overdue': overdue,
            },
            'today': {
                'total': today_visits,
                'completed': today_completed,
                'remaining': today_visits - today_completed,
            },
            'this_week': {
                'total': this_week_visits,
            },
            'by_state': state_counts,
            'partners': {
                'total': total_partners,
                'physicians': physicians,
                'safety_engineers': engineers,
            }
        }

    # ==================== WhatsApp Tools ====================

    def _tool_wfm_send_whatsapp(self, args):
        """Send a custom WhatsApp message to a partner."""
        if not args.get('partner_id') or not args.get('message'):
            return {'error': 'Both partner_id and message are required'}

        Partner = self.env['res.partner']
        WhatsApp = self.env['wfm.whatsapp.message']

        partner = Partner.browse(args['partner_id'])
        if not partner.exists():
            return {'error': f"Partner {args['partner_id']} not found"}

        phone = partner.mobile or partner.phone
        if not phone:
            return {'error': f"Partner {partner.name} has no phone number"}

        # Optional visit link
        visit_id = args.get('visit_id')
        visit = None
        if visit_id:
            visit = self.env['wfm.visit'].browse(visit_id)
            if not visit.exists():
                visit = None

        try:
            message = WhatsApp.send_message(
                partner_id=partner,
                message_body=args['message'],
                message_type='custom',
                visit_id=visit
            )

            if message and message.status == 'sent':
                return {
                    'success': True,
                    'message': f"WhatsApp sent to {partner.name}",
                    'recipient': partner.name,
                    'phone': phone,
                    'twilio_sid': message.twilio_sid,
                }
            else:
                error = message.error_message if message else 'Unknown error'
                return {
                    'success': False,
                    'error': f"Failed to send: {error}"
                }
        except Exception as e:
            return {'error': str(e)}

    def _tool_wfm_send_visit_notification(self, args):
        """Send a predefined WhatsApp notification for a visit."""
        if not args.get('visit_id'):
            return {'error': 'visit_id is required'}

        notification_type = args.get('type', 'assignment')
        valid_types = ['assignment', 'confirmed', 'reminder', 'cancelled']
        if notification_type not in valid_types:
            return {'error': f"Invalid type. Must be one of: {', '.join(valid_types)}"}

        Visit = self.env['wfm.visit']
        visit = Visit.browse(args['visit_id'])

        if not visit.exists():
            return {'error': f"Visit {args['visit_id']} not found"}

        if not visit.partner_id:
            return {'error': f"Visit {visit.name} has no partner assigned"}

        try:
            method_map = {
                'assignment': '_send_whatsapp_assignment',
                'confirmed': '_send_whatsapp_confirmed',
                'reminder': '_send_whatsapp_reminder',
                'cancelled': '_send_whatsapp_cancelled',
            }

            method = getattr(visit, method_map[notification_type])
            result = method()

            if result:
                return {
                    'success': True,
                    'message': f"{notification_type.title()} notification sent for {visit.name}",
                    'visit_reference': visit.name,
                    'recipient': visit.partner_id.name,
                    'type': notification_type,
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to send notification'
                }
        except Exception as e:
            return {'error': str(e)}

    def _tool_wfm_list_whatsapp_messages(self, args):
        """List WhatsApp message history."""
        WhatsApp = self.env['wfm.whatsapp.message']
        domain = []

        if args.get('visit_id'):
            domain.append(('visit_id', '=', args['visit_id']))

        if args.get('partner_id'):
            domain.append(('partner_id', '=', args['partner_id']))

        if args.get('status'):
            domain.append(('status', '=', args['status']))

        if args.get('message_type'):
            domain.append(('message_type', '=', args['message_type']))

        limit = args.get('limit', 10)
        messages = WhatsApp.search(domain, limit=limit, order='sent_at desc')

        result = []
        for m in messages:
            result.append({
                'id': m.id,
                'recipient': m.partner_id.name,
                'phone': m.phone,
                'type': m.message_type,
                'status': m.status,
                'sent_at': m.sent_at.strftime('%d/%m/%Y %H:%M') if m.sent_at else None,
                'visit_reference': m.visit_id.name if m.visit_id else None,
                'message_preview': (m.message_body[:100] + '...') if len(m.message_body or '') > 100 else m.message_body,
                'error': m.error_message if m.status == 'failed' else None,
            })

        return {
            'count': len(result),
            'messages': result
        }

    # ==================== Workflow Tools ====================

    def _tool_wfm_create_workflow(self, args):
        """Create a new autonomous workflow."""
        if not args.get('name') or not args.get('prompt'):
            return {'error': 'Both name and prompt are required'}

        Workflow = self.env['wfm.workflow']

        vals = {
            'name': args['name'],
            'prompt': args['prompt'],
        }

        if args.get('description'):
            vals['description'] = args['description']

        if args.get('schedule_type'):
            vals['schedule_type'] = args['schedule_type']

        if args.get('interval_number'):
            vals['interval_number'] = args['interval_number']

        if args.get('interval_type'):
            vals['interval_type'] = args['interval_type']

        if args.get('cron_expression'):
            vals['cron_expression'] = args['cron_expression']

        try:
            workflow = Workflow.create(vals)
            return {
                'success': True,
                'message': f"Created workflow '{workflow.name}' (ID: {workflow.id})",
                'workflow': {
                    'id': workflow.id,
                    'name': workflow.name,
                    'state': workflow.state,
                    'schedule_type': workflow.schedule_type,
                    'cron_description': workflow.cron_description,
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def _tool_wfm_list_workflows(self, args):
        """List existing workflows."""
        Workflow = self.env['wfm.workflow']
        domain = []

        if args.get('state'):
            domain.append(('state', '=', args['state']))

        limit = args.get('limit', 10)
        workflows = Workflow.search(domain, limit=limit, order='sequence, name')

        result = []
        for w in workflows:
            result.append({
                'id': w.id,
                'name': w.name,
                'description': w.description or '',
                'state': w.state,
                'schedule_type': w.schedule_type,
                'cron_description': w.cron_description or '',
                'last_run': w.last_run.strftime('%d/%m/%Y %H:%M') if w.last_run else None,
                'next_run': w.next_run.strftime('%d/%m/%Y %H:%M') if w.next_run else None,
                'run_count': w.run_count,
                'success_rate': f"{w.success_rate:.0f}%",
            })

        return {
            'count': len(result),
            'workflows': result
        }

    def _tool_wfm_update_workflow(self, args):
        """Update an existing workflow."""
        if not args.get('workflow_id'):
            return {'error': 'workflow_id is required'}

        Workflow = self.env['wfm.workflow']
        workflow = Workflow.browse(args['workflow_id'])

        if not workflow.exists():
            return {'error': f"Workflow {args['workflow_id']} not found"}

        vals = {}
        if args.get('name'):
            vals['name'] = args['name']
        if args.get('prompt'):
            vals['prompt'] = args['prompt']
        if args.get('schedule_type'):
            vals['schedule_type'] = args['schedule_type']
        if args.get('interval_number'):
            vals['interval_number'] = args['interval_number']
        if args.get('interval_type'):
            vals['interval_type'] = args['interval_type']
        if args.get('cron_expression'):
            vals['cron_expression'] = args['cron_expression']

        # Handle state changes via action methods
        state = args.get('state')
        if state == 'active' and workflow.state != 'active':
            workflow.action_activate()
        elif state == 'paused' and workflow.state == 'active':
            workflow.action_pause()

        if vals:
            workflow.write(vals)

        return {
            'success': True,
            'message': f"Updated workflow '{workflow.name}'",
            'workflow': {
                'id': workflow.id,
                'name': workflow.name,
                'state': workflow.state,
                'schedule_type': workflow.schedule_type,
                'cron_description': workflow.cron_description,
            }
        }

    def _tool_wfm_run_workflow(self, args):
        """Manually trigger a workflow."""
        if not args.get('workflow_id'):
            return {'error': 'workflow_id is required'}

        Workflow = self.env['wfm.workflow']
        workflow = Workflow.browse(args['workflow_id'])

        if not workflow.exists():
            return {'error': f"Workflow {args['workflow_id']} not found"}

        try:
            workflow.action_run_now()
            return {
                'success': True,
                'message': f"Triggered workflow '{workflow.name}'",
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
            }
        except Exception as e:
            return {'error': str(e)}

    def _tool_wfm_workflow_logs(self, args):
        """Get execution logs for a workflow."""
        WorkflowLog = self.env['wfm.workflow.log']
        domain = []

        if args.get('workflow_id'):
            domain.append(('workflow_id', '=', args['workflow_id']))

        if args.get('status'):
            domain.append(('status', '=', args['status']))

        limit = args.get('limit', 10)
        logs = WorkflowLog.search(domain, limit=limit, order='started_at desc')

        result = []
        for log in logs:
            result.append({
                'id': log.id,
                'workflow': log.workflow_id.name,
                'started_at': log.started_at.strftime('%d/%m/%Y %H:%M') if log.started_at else None,
                'ended_at': log.ended_at.strftime('%d/%m/%Y %H:%M') if log.ended_at else None,
                'duration_seconds': log.duration_seconds,
                'status': log.status,
                'tool_call_count': log.tool_call_count,
                'tokens_total': log.tokens_total,
                'error': log.error if log.status == 'failed' else None,
                'result_preview': (log.result[:200] + '...') if log.result and len(log.result) > 200 else log.result,
            })

        return {
            'count': len(result),
            'logs': result
        }

    # ==================== Churn Analysis Tools ====================

    def _tool_wfm_list_at_risk_partners(self, args):
        """List partners at risk of churning."""
        PartnerHealth = self.env['wfm.partner.health']
        domain = []

        # Filter by risk level
        risk_level = args.get('risk_level')
        if risk_level:
            domain.append(('risk_level', '=', risk_level))
        else:
            # Default: show high and critical risk
            domain.append(('risk_level', 'in', ['high', 'critical']))

        # Filter by ticket state
        ticket_state = args.get('ticket_state')
        if ticket_state:
            domain.append(('ticket_state', '=', ticket_state))

        # Filter by assigned coordinator
        if args.get('my_tickets'):
            domain.append(('assigned_coordinator_id', '=', self.env.uid))

        limit = args.get('limit', 20)
        health_records = PartnerHealth.search(domain, limit=limit, order='churn_risk_score desc')

        result = []
        for h in health_records:
            result.append({
                'id': h.id,
                'partner_id': h.partner_id.id,
                'partner_name': h.partner_id.name,
                'specialty': h.partner_id.specialty if hasattr(h.partner_id, 'specialty') else None,
                'risk_score': round(h.churn_risk_score, 1),
                'risk_level': h.risk_level,
                'ticket_state': h.ticket_state,
                'assigned_to': h.assigned_coordinator_id.name if h.assigned_coordinator_id else None,
                'days_since_last_visit': h.days_since_last_visit,
                'visits_declined_30d': h.visits_declined_30d,
                'risk_trend': h.risk_trend,
            })

        return {
            'count': len(result),
            'at_risk_partners': result,
            'summary': {
                'critical': len([r for r in result if r['risk_level'] == 'critical']),
                'high': len([r for r in result if r['risk_level'] == 'high']),
            }
        }

    def _tool_wfm_get_partner_health(self, args):
        """Get detailed churn risk analysis for a partner."""
        if not args.get('partner_id') and not args.get('health_id'):
            return {'error': 'Either partner_id or health_id is required'}

        PartnerHealth = self.env['wfm.partner.health']

        if args.get('health_id'):
            health = PartnerHealth.browse(args['health_id'])
        else:
            health = PartnerHealth.search([
                ('partner_id', '=', args['partner_id'])
            ], order='computed_date desc', limit=1)

        if not health or not health.exists():
            return {'error': 'No health record found for this partner'}

        # Get score breakdown
        score_breakdown = {
            'decline_rate': {
                'score': round(health.decline_rate_score, 1),
                'max': 30,
                'detail': f"{health.visits_declined_30d or 0} visits declined out of {health.visits_assigned_30d or 0} assigned"
            },
            'volume_change': {
                'score': round(health.volume_change_score, 1),
                'max': 25,
                'detail': f"Last 30d: {health.visits_last_30d or 0}, Previous 30d: {health.visits_previous_30d or 0}"
            },
            'inactivity': {
                'score': round(health.inactivity_score, 1),
                'max': 20,
                'detail': f"{health.days_since_last_visit or 0} days since last visit"
            },
            'payment_issues': {
                'score': round(health.payment_issue_score, 1),
                'max': 15,
                'detail': f"{health.payment_complaints or 0} payment complaints"
            },
            'negative_feedback': {
                'score': round(health.feedback_score, 1),
                'max': 10,
                'detail': f"{health.negative_feedback_count or 0} negative feedback items"
            },
        }

        return {
            'health_id': health.id,
            'partner': {
                'id': health.partner_id.id,
                'name': health.partner_id.name,
                'phone': health.partner_id.phone or '',
                'email': health.partner_id.email or '',
            },
            'computed_date': health.computed_date.strftime('%d/%m/%Y') if health.computed_date else None,
            'risk_score': round(health.churn_risk_score, 1),
            'risk_level': health.risk_level,
            'risk_trend': health.risk_trend,
            'score_breakdown': score_breakdown,
            'ticket': {
                'state': health.ticket_state,
                'assigned_to': health.assigned_coordinator_id.name if health.assigned_coordinator_id else None,
                'planned_action': health.planned_action,
            },
            'ai_advice': health.ai_advice_text or None,
        }

    def _tool_wfm_log_retention_action(self, args):
        """Log a retention intervention/action for a partner."""
        if not args.get('health_id') or not args.get('intervention_type'):
            return {'error': 'Both health_id and intervention_type are required'}

        PartnerHealth = self.env['wfm.partner.health']
        Intervention = self.env['wfm.partner.intervention']

        health = PartnerHealth.browse(args['health_id'])
        if not health.exists():
            return {'error': f"Health record {args['health_id']} not found"}

        valid_types = ['call', 'whatsapp', 'email', 'meeting', 'bonus', 'workload']
        if args['intervention_type'] not in valid_types:
            return {'error': f"Invalid intervention_type. Must be one of: {', '.join(valid_types)}"}

        # Create intervention record
        intervention_vals = {
            'health_id': health.id,
            'partner_id': health.partner_id.id,
            'intervention_type': args['intervention_type'],
            'notes': args.get('notes', ''),
            'coordinator_id': self.env.uid,
        }

        if args.get('outcome'):
            valid_outcomes = ['positive', 'neutral', 'negative', 'pending']
            if args['outcome'] in valid_outcomes:
                intervention_vals['outcome'] = args['outcome']

        try:
            intervention = Intervention.create(intervention_vals)

            # Update ticket state to in_progress if it was open
            if health.ticket_state == 'open':
                health.write({'ticket_state': 'in_progress'})

            return {
                'success': True,
                'message': f"Logged {args['intervention_type']} intervention for {health.partner_id.name}",
                'intervention_id': intervention.id,
                'partner_name': health.partner_id.name,
                'ticket_state': health.ticket_state,
            }
        except Exception as e:
            return {'error': str(e)}

    def _tool_wfm_resolve_retention_ticket(self, args):
        """Resolve a retention ticket with outcome."""
        if not args.get('health_id') or not args.get('outcome'):
            return {'error': 'Both health_id and outcome are required'}

        PartnerHealth = self.env['wfm.partner.health']
        health = PartnerHealth.browse(args['health_id'])

        if not health.exists():
            return {'error': f"Health record {args['health_id']} not found"}

        valid_outcomes = ['retained', 'churned', 'false_alarm']
        if args['outcome'] not in valid_outcomes:
            return {'error': f"Invalid outcome. Must be one of: {', '.join(valid_outcomes)}"}

        try:
            health.write({
                'ticket_state': 'resolved',
                'resolution_outcome': args['outcome'],
                'resolution_notes': args.get('notes', ''),
                'resolution_date': fields.Datetime.now(),
            })

            return {
                'success': True,
                'message': f"Resolved ticket for {health.partner_id.name} as {args['outcome']}",
                'partner_name': health.partner_id.name,
                'outcome': args['outcome'],
            }
        except Exception as e:
            return {'error': str(e)}

    def _tool_wfm_churn_dashboard_stats(self, args):
        """Get churn analysis dashboard statistics."""
        PartnerHealth = self.env['wfm.partner.health']

        # Get counts by risk level
        critical = PartnerHealth.search_count([('risk_level', '=', 'critical')])
        high = PartnerHealth.search_count([('risk_level', '=', 'high')])
        medium = PartnerHealth.search_count([('risk_level', '=', 'medium')])
        low = PartnerHealth.search_count([('risk_level', '=', 'low')])

        # Get ticket stats
        open_tickets = PartnerHealth.search_count([
            ('ticket_state', '=', 'open'),
            ('risk_level', 'in', ['high', 'critical'])
        ])
        in_progress = PartnerHealth.search_count([('ticket_state', '=', 'in_progress')])
        resolved_retained = PartnerHealth.search_count([
            ('resolution_outcome', '=', 'retained')
        ])
        resolved_churned = PartnerHealth.search_count([
            ('resolution_outcome', '=', 'churned')
        ])

        # Get trend data
        improving = PartnerHealth.search_count([('risk_trend', '=', 'improving')])
        declining = PartnerHealth.search_count([('risk_trend', '=', 'declining')])

        # Calculate retention rate
        total_resolved = resolved_retained + resolved_churned
        retention_rate = (resolved_retained / total_resolved * 100) if total_resolved > 0 else 0

        return {
            'risk_distribution': {
                'critical': critical,
                'high': high,
                'medium': medium,
                'low': low,
                'total_at_risk': critical + high,
            },
            'tickets': {
                'open': open_tickets,
                'in_progress': in_progress,
                'resolved_retained': resolved_retained,
                'resolved_churned': resolved_churned,
            },
            'trends': {
                'improving': improving,
                'declining': declining,
            },
            'retention_rate': f"{retention_rate:.1f}%",
        }

    def _tool_wfm_get_ai_retention_strategy(self, args):
        """Get AI-powered retention strategy for a partner."""
        if not args.get('health_id'):
            return {'error': 'health_id is required'}

        PartnerHealth = self.env['wfm.partner.health']
        AIEngine = self.env['wfm.ai.retention.engine']

        health = PartnerHealth.browse(args['health_id'])
        if not health.exists():
            return {'error': f"Health record {args['health_id']} not found"}

        try:
            # Call the AI retention engine
            engine = AIEngine.search([], limit=1) or AIEngine.create({'name': 'Default'})
            result = engine.generate_retention_strategy(health)

            if result.get('error'):
                return {'error': result['error']}

            # Store the advice on the health record
            if result.get('advice'):
                health.write({'ai_advice_text': result['advice']})

            return {
                'success': True,
                'partner_name': health.partner_id.name,
                'risk_level': health.risk_level,
                'risk_score': round(health.churn_risk_score, 1),
                'ai_strategy': result.get('advice', ''),
                'recommended_action': result.get('recommended_action', ''),
                'whatsapp_message': result.get('whatsapp_message', ''),
                'urgency': result.get('urgency', 'medium'),
            }
        except Exception as e:
            return {'error': str(e)}

    def _tool_wfm_run_churn_computation(self, args):
        """Trigger churn risk computation for all partners."""
        PartnerHealth = self.env['wfm.partner.health']

        try:
            # Call the cron method to compute health for all partners
            PartnerHealth._cron_compute_partner_health()

            # Get summary
            critical = PartnerHealth.search_count([('risk_level', '=', 'critical')])
            high = PartnerHealth.search_count([('risk_level', '=', 'high')])

            return {
                'success': True,
                'message': 'Churn risk computation completed for all partners',
                'summary': {
                    'critical_risk': critical,
                    'high_risk': high,
                    'total_at_risk': critical + high,
                }
            }
        except Exception as e:
            return {'error': str(e)}
