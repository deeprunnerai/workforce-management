from odoo import models, fields, api
from odoo.models import Constraint
from datetime import timedelta


class WfmPartnerHealth(models.Model):
    """
    Partner Health & Churn Prediction Model

    Tracks partner engagement metrics and computes churn risk score
    to enable proactive intervention before partners leave.

    Risk Score (0-100): Higher = more likely to churn
    - Decline rate (30 days): up to 30 points
    - Visit volume change: up to 25 points
    - Days since last activity: up to 20 points
    - Payment/complaint issues: up to 15 points
    - Negative feedback: up to 10 points
    """
    _name = 'wfm.partner.health'
    _description = 'Partner Health & Churn Prediction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'churn_risk_score desc'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        domain=[('is_wfm_partner', '=', True)],
        index=True
    )
    computed_date = fields.Date(
        string='Computed Date',
        default=fields.Date.today,
        required=True
    )

    # ===== RAW METRICS =====
    # Visit metrics (30 days)
    visits_last_30d = fields.Integer(
        string='Visits (Last 30 Days)',
        help='Number of completed visits in the last 30 days'
    )
    visits_previous_30d = fields.Integer(
        string='Visits (Previous 30 Days)',
        help='Number of completed visits in the 30 days before last 30'
    )
    visits_declined_30d = fields.Integer(
        string='Visits Declined (30 Days)',
        help='Number of visits declined/cancelled in last 30 days'
    )
    visits_assigned_30d = fields.Integer(
        string='Visits Assigned (30 Days)',
        help='Total visits assigned in last 30 days'
    )

    # Activity metrics
    days_since_last_visit = fields.Integer(
        string='Days Since Last Visit',
        help='Days since partner completed a visit'
    )
    days_since_last_login = fields.Integer(
        string='Days Since Last Login',
        help='Days since partner logged into the system'
    )

    # Performance metrics
    avg_rating_30d = fields.Float(
        string='Avg Rating (30 Days)',
        digits=(2, 1),
        help='Average client rating in last 30 days'
    )
    on_time_rate_30d = fields.Float(
        string='On-Time Rate (30 Days)',
        digits=(5, 2),
        help='Percentage of visits completed on time'
    )

    # Issue metrics
    payment_complaints = fields.Integer(
        string='Payment Complaints',
        help='Number of payment-related complaints in last 90 days'
    )
    negative_feedback_count = fields.Integer(
        string='Negative Feedback',
        help='Number of negative feedback items in last 90 days'
    )

    # ===== COMPUTED SCORES =====
    decline_rate_score = fields.Float(
        string='Decline Rate Score',
        compute='_compute_component_scores',
        store=True,
        help='Score based on visit decline rate (0-30)'
    )
    volume_change_score = fields.Float(
        string='Volume Change Score',
        compute='_compute_component_scores',
        store=True,
        help='Score based on visit volume change (0-25)'
    )
    inactivity_score = fields.Float(
        string='Inactivity Score',
        compute='_compute_component_scores',
        store=True,
        help='Score based on days since activity (0-20)'
    )
    payment_issue_score = fields.Float(
        string='Payment Issue Score',
        compute='_compute_component_scores',
        store=True,
        help='Score based on payment complaints (0-15)'
    )
    feedback_score = fields.Float(
        string='Feedback Score',
        compute='_compute_component_scores',
        store=True,
        help='Score based on negative feedback (0-10)'
    )

    # ===== FINAL CHURN RISK =====
    churn_risk_score = fields.Float(
        string='Churn Risk Score',
        compute='_compute_churn_risk',
        store=True,
        help='Overall churn risk score (0-100). Higher = more likely to churn.'
    )
    risk_level = fields.Selection([
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🟠 High'),
        ('critical', '🔴 Critical'),
    ], string='Risk Level', compute='_compute_risk_level', store=True)

    # ===== TREND =====
    previous_risk_score = fields.Float(
        string='Previous Risk Score',
        help='Risk score from previous computation'
    )
    risk_trend = fields.Selection([
        ('improving', '📈 Improving'),
        ('stable', '➡️ Stable'),
        ('declining', '📉 Declining'),
    ], string='Risk Trend', compute='_compute_risk_trend', store=True)

    # ===== TICKET WORKFLOW =====
    ticket_state = fields.Selection([
        ('open', '🎫 Open'),
        ('in_progress', '🔄 In Progress'),
        ('resolved', '✅ Resolved'),
        ('closed', '🔒 Closed'),
    ], string='Ticket Status', default='open', tracking=True)

    # Planned action (coordinator's choice)
    planned_action = fields.Selection([
        ('call', '📞 Phone Call'),
        ('whatsapp', '💬 WhatsApp'),
        ('email', '📧 Email'),
        ('meeting', '🤝 In-Person Meeting'),
        ('bonus', '💰 Bonus/Incentive'),
        ('workload', '📊 Workload Adjustment'),
    ], string='Planned Action', tracking=True)

    assigned_coordinator_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        tracking=True,
        default=lambda self: self.env.user
    )

    # Resolution
    resolution_date = fields.Datetime(string='Resolution Date', readonly=True)
    resolution_notes = fields.Text(string='Resolution Notes')
    resolution_outcome = fields.Selection([
        ('retained', '🎉 Partner Retained'),
        ('churned', '💔 Partner Left'),
        ('false_alarm', '✓ False Alarm'),
    ], string='Resolution Outcome', tracking=True)

    # Final Verdict (shown in list views for quick overview)
    final_verdict = fields.Selection([
        ('retained', '🎉 Retained'),
        ('churned', '💔 Churned'),
        ('in_progress', '🔄 In Progress'),
        ('pending', '⏳ Pending'),
    ], string='Final Verdict', compute='_compute_final_verdict', store=True)

    # Legacy fields for backward compatibility
    needs_intervention = fields.Boolean(
        string='Needs Intervention',
        compute='_compute_needs_intervention',
        store=True
    )
    intervention_ids = fields.One2many(
        'wfm.partner.intervention',
        'health_id',
        string='Action Log'
    )
    last_intervention_date = fields.Date(
        string='Last Action',
        compute='_compute_last_intervention'
    )

    # Related fields for quick actions
    partner_phone = fields.Char(
        related='partner_id.phone',
        string='Partner Phone'
    )
    partner_mobile = fields.Char(
        compute='_compute_partner_mobile',
        string='Partner Mobile'
    )
    partner_email = fields.Char(
        related='partner_id.email',
        string='Partner Email'
    )

    # AI Advice - populated when user clicks "Ask AI"
    ai_advice_text = fields.Text(
        string='AI Advice',
        help='AI-generated suggestion displayed on the form'
    )

    @api.depends('partner_id')
    def _compute_partner_mobile(self):
        """Get mobile from partner if field exists, else use phone"""
        for record in self:
            if record.partner_id:
                # Check if mobile field exists on partner
                if hasattr(record.partner_id, 'mobile') and record.partner_id.mobile:
                    record.partner_mobile = record.partner_id.mobile
                else:
                    record.partner_mobile = record.partner_id.phone
            else:
                record.partner_mobile = False

    @api.depends('decline_rate_score', 'volume_change_score', 'inactivity_score',
                 'payment_issue_score', 'feedback_score', 'risk_level')
    def _compute_ai_suggestion(self):
        """
        AI Advisor: Analyze risk factors and suggest the best action.
        This is a rule-based recommendation engine that looks at the
        dominant risk factor to suggest the most appropriate intervention.
        """
        for record in self:
            # Default suggestion
            action = 'call'
            reason = "Start with a phone call to understand the partner's concerns."

            # Find the dominant risk factor
            scores = {
                'decline': record.decline_rate_score or 0,
                'volume': record.volume_change_score or 0,
                'inactivity': record.inactivity_score or 0,
                'payment': record.payment_issue_score or 0,
                'feedback': record.feedback_score or 0,
            }

            dominant_factor = max(scores, key=scores.get) if any(scores.values()) else None

            # Generate suggestion based on dominant risk factor
            if dominant_factor == 'decline' and scores['decline'] >= 15:
                action = 'workload'
                reason = (
                    f"Partner declined {record.visits_declined_30d or 0} visits recently. "
                    "They may be overwhelmed or have scheduling conflicts. "
                    "Review and adjust their workload to better fit their availability."
                )
            elif dominant_factor == 'inactivity' and scores['inactivity'] >= 15:
                if record.days_since_last_visit and record.days_since_last_visit > 30:
                    action = 'meeting'
                    reason = (
                        f"Partner inactive for {record.days_since_last_visit} days. "
                        "An in-person meeting shows commitment and helps rebuild the relationship. "
                        "Personal touch works best for re-engagement."
                    )
                else:
                    action = 'call'
                    reason = (
                        f"Partner showing early signs of disengagement. "
                        "A quick call to check in and understand any issues before they escalate."
                    )
            elif dominant_factor == 'payment' and scores['payment'] >= 10:
                action = 'bonus'
                reason = (
                    f"Partner has {record.payment_complaints or 0} payment-related complaints. "
                    "Consider discussing compensation, offering a bonus, or reviewing payment terms. "
                    "Financial concerns are often a key driver of churn."
                )
            elif dominant_factor == 'volume' and scores['volume'] >= 15:
                action = 'call'
                reason = (
                    "Visit volume dropped significantly compared to previous period. "
                    "Call to understand if there are issues with client assignments, "
                    "travel requirements, or personal circumstances."
                )
            elif dominant_factor == 'feedback' and scores['feedback'] >= 5:
                action = 'meeting'
                reason = (
                    f"Partner received {record.negative_feedback_count or 0} negative feedback items. "
                    "Meet to discuss concerns, provide support, and create improvement plan. "
                    "Show you care about their success."
                )
            elif record.risk_level == 'critical':
                action = 'call'
                reason = (
                    "CRITICAL risk level - immediate action required! "
                    "Call the partner today to understand their situation and prevent churn. "
                    "Be prepared to offer solutions."
                )
            elif record.risk_level == 'high':
                action = 'whatsapp'
                reason = (
                    "High risk level. Send a WhatsApp message as a quick touchpoint. "
                    "It's less intrusive than a call but more personal than email. "
                    "Opens the door for further conversation."
                )
            elif record.risk_level == 'medium':
                action = 'email'
                reason = (
                    "Medium risk - proactive outreach recommended. "
                    "Send a friendly check-in email to maintain the relationship "
                    "and show you value their partnership."
                )
            else:
                action = 'email'
                reason = (
                    "Low risk - maintain relationship with periodic check-ins. "
                    "A brief email keeps communication open without being intrusive."
                )

            record.ai_suggested_action = action
            record.ai_suggestion_reason = reason

    _partner_date_unique = Constraint(
        'UNIQUE(partner_id, computed_date)',
        'Health record already exists for this partner and date.'
    )

    @api.depends('visits_declined_30d', 'visits_assigned_30d', 'visits_last_30d',
                 'visits_previous_30d', 'days_since_last_visit', 'days_since_last_login',
                 'payment_complaints', 'negative_feedback_count')
    def _compute_component_scores(self):
        """Compute individual component scores for the churn risk"""
        for record in self:
            # 1. Decline Rate Score (0-30 points)
            # If partner declined >50% of assigned visits, high risk
            if record.visits_assigned_30d > 0:
                decline_rate = (record.visits_declined_30d / record.visits_assigned_30d) * 100
                record.decline_rate_score = min(decline_rate * 0.6, 30)
            else:
                record.decline_rate_score = 0

            # 2. Volume Change Score (0-25 points)
            # Significant drop in visit volume indicates disengagement
            if record.visits_previous_30d > 0:
                volume_change = ((record.visits_previous_30d - record.visits_last_30d)
                                / record.visits_previous_30d) * 100
                # Only penalize for drops, not increases
                record.volume_change_score = min(max(volume_change * 0.5, 0), 25)
            elif record.visits_last_30d == 0:
                # No recent activity and no previous baseline
                record.volume_change_score = 15
            else:
                record.volume_change_score = 0

            # 3. Inactivity Score (0-20 points)
            # Days since last activity (visit or login)
            days_inactive = min(record.days_since_last_visit, record.days_since_last_login or 999)
            if days_inactive > 60:
                record.inactivity_score = 20
            elif days_inactive > 30:
                record.inactivity_score = 15
            elif days_inactive > 14:
                record.inactivity_score = 10
            elif days_inactive > 7:
                record.inactivity_score = 5
            else:
                record.inactivity_score = 0

            # 4. Payment Issue Score (0-15 points)
            record.payment_issue_score = min(record.payment_complaints * 5, 15)

            # 5. Negative Feedback Score (0-10 points)
            record.feedback_score = min(record.negative_feedback_count * 3, 10)

    @api.depends('decline_rate_score', 'volume_change_score', 'inactivity_score',
                 'payment_issue_score', 'feedback_score')
    def _compute_churn_risk(self):
        """Compute overall churn risk score (0-100)"""
        for record in self:
            record.churn_risk_score = (
                record.decline_rate_score +
                record.volume_change_score +
                record.inactivity_score +
                record.payment_issue_score +
                record.feedback_score
            )

    @api.depends('churn_risk_score')
    def _compute_risk_level(self):
        """Convert numeric score to risk level category"""
        for record in self:
            score = record.churn_risk_score
            if score >= 70:
                record.risk_level = 'critical'
            elif score >= 50:
                record.risk_level = 'high'
            elif score >= 30:
                record.risk_level = 'medium'
            else:
                record.risk_level = 'low'

    @api.depends('ticket_state', 'resolution_outcome')
    def _compute_final_verdict(self):
        """Compute final verdict based on ticket state and resolution outcome"""
        for record in self:
            if record.resolution_outcome == 'retained':
                record.final_verdict = 'retained'
            elif record.resolution_outcome == 'churned':
                record.final_verdict = 'churned'
            elif record.ticket_state in ('in_progress', 'open'):
                if record.ticket_state == 'in_progress':
                    record.final_verdict = 'in_progress'
                else:
                    record.final_verdict = 'pending'
            elif record.resolution_outcome == 'false_alarm':
                record.final_verdict = 'retained'  # False alarm = still retained
            else:
                record.final_verdict = 'pending'

    @api.depends('churn_risk_score', 'previous_risk_score')
    def _compute_risk_trend(self):
        """Determine if risk is improving, stable, or declining"""
        for record in self:
            if not record.previous_risk_score:
                record.risk_trend = 'stable'
            elif record.churn_risk_score < record.previous_risk_score - 5:
                record.risk_trend = 'improving'
            elif record.churn_risk_score > record.previous_risk_score + 5:
                record.risk_trend = 'declining'
            else:
                record.risk_trend = 'stable'

    @api.depends('risk_level', 'last_intervention_date')
    def _compute_needs_intervention(self):
        """Determine if partner needs proactive intervention"""
        for record in self:
            if record.risk_level in ('high', 'critical'):
                # Check if intervention was done recently (within 14 days)
                if record.last_intervention_date:
                    days_since = (fields.Date.today() - record.last_intervention_date).days
                    record.needs_intervention = days_since > 14
                else:
                    record.needs_intervention = True
            else:
                record.needs_intervention = False

    def _compute_last_intervention(self):
        """Get date of last intervention"""
        for record in self:
            last = self.env['wfm.partner.intervention'].search([
                ('health_id', '=', record.id)
            ], order='date desc', limit=1)
            record.last_intervention_date = last.date if last else False

    @api.model
    def compute_partner_health(self, partner_id):
        """
        Compute health metrics for a specific partner.
        Called by cron job or manually.
        """
        partner = self.env['res.partner'].browse(partner_id)
        if not partner.exists() or not partner.is_wfm_partner:
            return False

        today = fields.Date.today()
        thirty_days_ago = today - timedelta(days=30)
        sixty_days_ago = today - timedelta(days=60)
        ninety_days_ago = today - timedelta(days=90)

        Visit = self.env['wfm.visit']

        # Get visit statistics
        visits_last_30d = Visit.search_count([
            ('partner_id', '=', partner_id),
            ('state', '=', 'done'),
            ('visit_date', '>=', thirty_days_ago),
            ('visit_date', '<=', today),
        ])

        visits_previous_30d = Visit.search_count([
            ('partner_id', '=', partner_id),
            ('state', '=', 'done'),
            ('visit_date', '>=', sixty_days_ago),
            ('visit_date', '<', thirty_days_ago),
        ])

        visits_declined_30d = Visit.search_count([
            ('partner_id', '=', partner_id),
            ('state', '=', 'cancelled'),
            ('visit_date', '>=', thirty_days_ago),
        ])

        visits_assigned_30d = Visit.search_count([
            ('partner_id', '=', partner_id),
            ('visit_date', '>=', thirty_days_ago),
        ])

        # Days since last visit
        last_visit = Visit.search([
            ('partner_id', '=', partner_id),
            ('state', '=', 'done'),
        ], order='visit_date desc', limit=1)

        if last_visit:
            days_since_last_visit = (today - last_visit.visit_date).days
        else:
            days_since_last_visit = 999  # Never completed a visit

        # Days since last login (from res.users if partner has user)
        days_since_last_login = 999
        if partner.user_ids:
            user = partner.user_ids[0]
            if user.login_date:
                days_since_last_login = (today - user.login_date.date()).days

        # Get previous health record for trend
        previous_health = self.search([
            ('partner_id', '=', partner_id),
            ('computed_date', '<', today),
        ], order='computed_date desc', limit=1)

        previous_risk_score = previous_health.churn_risk_score if previous_health else 0

        # Create or update health record
        existing = self.search([
            ('partner_id', '=', partner_id),
            ('computed_date', '=', today),
        ], limit=1)

        values = {
            'partner_id': partner_id,
            'computed_date': today,
            'visits_last_30d': visits_last_30d,
            'visits_previous_30d': visits_previous_30d,
            'visits_declined_30d': visits_declined_30d,
            'visits_assigned_30d': visits_assigned_30d,
            'days_since_last_visit': days_since_last_visit,
            'days_since_last_login': days_since_last_login,
            'payment_complaints': 0,  # TODO: Integrate with complaints model
            'negative_feedback_count': 0,  # TODO: Integrate with feedback model
            'previous_risk_score': previous_risk_score,
        }

        if existing:
            existing.write(values)
            return existing
        else:
            return self.create(values)

    @api.model
    def _cron_compute_all_partner_health(self):
        """
        Cron job to compute health scores for all active partners.
        Runs daily to keep churn predictions fresh.
        """
        partners = self.env['res.partner'].search([
            ('is_wfm_partner', '=', True),
            ('active', '=', True),
        ])

        critical_partners = []
        high_risk_partners = []

        for partner in partners:
            try:
                health = self.compute_partner_health(partner.id)
                if health:
                    if health.risk_level == 'critical' and health.needs_intervention:
                        critical_partners.append(health)
                    elif health.risk_level == 'high' and health.needs_intervention:
                        high_risk_partners.append(health)
            except Exception as e:
                # Log error but continue with other partners
                self.env.cr.rollback()
                continue

        # Send alerts for critical and high-risk partners
        if critical_partners or high_risk_partners:
            self._send_risk_alerts(critical_partners, high_risk_partners)

        return True

    def _send_risk_alerts(self, critical_partners, high_risk_partners):
        """
        Send notifications to coordinators about at-risk partners.
        Creates activities for follow-up.
        """
        # Get coordinators (users with specific group or all internal users)
        coordinators = self.env['res.users'].search([
            ('share', '=', False),
            ('active', '=', True),
        ], limit=5)  # Limit to first 5 coordinators

        if not coordinators:
            return

        # Build alert message
        message_parts = []

        if critical_partners:
            message_parts.append(f"🔴 <b>CRITICAL RISK ({len(critical_partners)} partners):</b><br/>")
            for health in critical_partners[:5]:  # Limit to 5
                message_parts.append(
                    f"• {health.partner_id.name} - Score: {health.churn_risk_score:.0f}/100<br/>"
                )

        if high_risk_partners:
            message_parts.append(f"<br/>🟠 <b>HIGH RISK ({len(high_risk_partners)} partners):</b><br/>")
            for health in high_risk_partners[:5]:  # Limit to 5
                message_parts.append(
                    f"• {health.partner_id.name} - Score: {health.churn_risk_score:.0f}/100<br/>"
                )

        message_parts.append(
            "<br/><a href='/web#action=wfm_fsm.action_at_risk_partners'>View All At-Risk Partners →</a>"
        )

        message = ''.join(message_parts)

        # Create activity for first coordinator
        if critical_partners:
            first_critical = critical_partners[0]
            self.env['mail.activity'].create({
                'res_model_id': self.env['ir.model']._get('wfm.partner.health').id,
                'res_id': first_critical.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': f'🔴 {len(critical_partners)} Critical Risk Partners Need Intervention',
                'note': message,
                'user_id': coordinators[0].id,
                'date_deadline': fields.Date.today(),
            })

        # Post message to first critical partner's chatter
        for health in critical_partners[:3]:
            health.message_post(
                body=f"⚠️ <b>Churn Risk Alert</b><br/>"
                     f"Partner {health.partner_id.name} has reached CRITICAL risk level "
                     f"(Score: {health.churn_risk_score:.0f}/100). Immediate intervention recommended.",
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

    def action_view_partner(self):
        """Open the partner form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_intervention(self):
        """Open wizard to log an action"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wfm.partner.intervention',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_health_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_intervention_type': self.planned_action or 'call',
            },
        }

    # ===== TICKET WORKFLOW ACTIONS =====
    def action_start_work(self):
        """Coordinator starts working on this ticket"""
        self.ensure_one()
        self.write({
            'ticket_state': 'in_progress',
            'assigned_coordinator_id': self.env.user.id,
        })
        self.message_post(
            body=f"🔄 Ticket picked up by {self.env.user.name}",
            message_type='notification',
        )

    def action_mark_resolved(self):
        """Open resolution wizard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wfm.partner.health',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'views': [(self.env.ref('wfm_fsm.view_partner_health_resolve_wizard').id, 'form')],
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_resolve_retained(self):
        """Quick resolve: Partner Retained"""
        self.ensure_one()
        self.write({
            'ticket_state': 'resolved',
            'resolution_outcome': 'retained',
            'resolution_date': fields.Datetime.now(),
        })
        self.message_post(
            body=f"🎉 <b>Partner Retained!</b> Resolved by {self.env.user.name}",
            message_type='notification',
        )

    def action_resolve_churned(self):
        """Quick resolve: Partner Churned"""
        self.ensure_one()
        self.write({
            'ticket_state': 'resolved',
            'resolution_outcome': 'churned',
            'resolution_date': fields.Datetime.now(),
        })
        self.message_post(
            body=f"💔 <b>Partner Left</b> - Marked by {self.env.user.name}",
            message_type='notification',
        )

    def action_close_ticket(self):
        """Close the ticket (final state)"""
        self.ensure_one()
        if self.ticket_state != 'resolved':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Cannot Close',
                    'message': 'Resolve the ticket first before closing',
                    'type': 'warning',
                }
            }
        self.write({'ticket_state': 'closed'})
        self.message_post(
            body=f"🔒 Ticket closed by {self.env.user.name}",
            message_type='notification',
        )

    def action_reopen_ticket(self):
        """Reopen a closed or resolved ticket"""
        self.ensure_one()
        self.write({
            'ticket_state': 'open',
            'resolution_outcome': False,
            'resolution_date': False,
        })
        self.message_post(
            body=f"🔄 Ticket reopened by {self.env.user.name}",
            message_type='notification',
        )

    # ===== QUICK ACTION METHODS =====
    def action_call_partner(self):
        """Open tel: link to call the partner"""
        self.ensure_one()
        phone = self.partner_mobile or self.partner_phone
        if not phone:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Phone Number',
                    'message': f'{self.partner_id.name} has no phone number configured',
                    'type': 'warning',
                }
            }

        # Clean phone number
        clean_phone = ''.join(filter(str.isdigit, phone))
        # Add Greece country code if not present
        if not clean_phone.startswith('30') and len(clean_phone) == 10:
            clean_phone = '30' + clean_phone

        # Log the action attempt
        self.message_post(
            body=f"📞 Initiated call to {phone}",
            message_type='notification',
        )

        return {
            'type': 'ir.actions.act_url',
            'url': f'tel:{clean_phone}',
            'target': 'self',
        }

    def action_open_whatsapp(self):
        """Open WhatsApp with pre-filled message"""
        self.ensure_one()
        import urllib.parse

        phone = self.partner_mobile or self.partner_phone
        if not phone:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Phone Number',
                    'message': f'{self.partner_id.name} has no phone number configured',
                    'type': 'warning',
                }
            }

        # Clean phone number
        clean_phone = ''.join(filter(str.isdigit, phone))
        # Add Greece country code if not present
        if not clean_phone.startswith('30') and len(clean_phone) == 10:
            clean_phone = '30' + clean_phone

        # Create a simple greeting message in Greek
        partner_name = self.partner_id.name.split()[0] if self.partner_id.name else 'εσάς'
        message = f"Γεια σας {partner_name}, θα ήθελα να συζητήσουμε μαζί σας. Πότε θα σας βόλευε;"

        # Use AI-generated message if available
        if self.ai_whatsapp_message:
            message = self.ai_whatsapp_message

        encoded_msg = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"

        # Log the action
        self.message_post(
            body=f"💬 Opened WhatsApp for {self.partner_id.name}",
            message_type='notification',
        )

        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }

    def action_send_email(self):
        """Open email composer for the partner"""
        self.ensure_one()

        if not self.partner_email:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Email Address',
                    'message': f'{self.partner_id.name} has no email configured',
                    'type': 'warning',
                }
            }

        # Try to use Odoo's email composer if available
        try:
            template = self.env.ref('wfm_fsm.email_template_retention_outreach', raise_if_not_found=False)
            compose_form = self.env.ref('mail.email_compose_message_wizard_form', raise_if_not_found=False)

            if compose_form:
                ctx = {
                    'default_model': 'wfm.partner.health',
                    'default_res_ids': self.ids,
                    'default_partner_ids': [(4, self.partner_id.id)],
                    'default_composition_mode': 'comment',
                    'default_email_from': self.env.user.email or self.env.company.email,
                }
                if template:
                    ctx['default_template_id'] = template.id

                return {
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(compose_form.id, 'form')],
                    'view_id': compose_form.id,
                    'target': 'new',
                    'context': ctx,
                }
        except Exception:
            pass

        # Fallback: open mailto link
        import urllib.parse
        partner_name = self.partner_id.name.split()[0] if self.partner_id.name else ''
        subject = urllib.parse.quote(f"GEP Group - Επικοινωνία με {partner_name}")
        body = urllib.parse.quote(f"Αγαπητέ/ή {partner_name},\n\nΘα ήθελα να επικοινωνήσω μαζί σας σχετικά με τη συνεργασία μας.\n\nΜε εκτίμηση,\n{self.env.user.name}")

        mailto_url = f"mailto:{self.partner_email}?subject={subject}&body={body}"

        self.message_post(
            body=f"📧 Opened email for {self.partner_id.name}",
            message_type='notification',
        )

        return {
            'type': 'ir.actions.act_url',
            'url': mailto_url,
            'target': 'self',
        }

    def action_schedule_meeting(self):
        """Create a calendar event with Google Meet link"""
        self.ensure_one()

        # Try to create an Odoo calendar event
        try:
            # Check if calendar module is installed
            CalendarEvent = self.env.get('calendar.event')
            if CalendarEvent is not None:
                # Create calendar event
                from datetime import datetime, timedelta
                meeting_start = datetime.now() + timedelta(days=1)
                meeting_start = meeting_start.replace(hour=10, minute=0, second=0, microsecond=0)
                meeting_end = meeting_start + timedelta(hours=1)

                event_vals = {
                    'name': f'Retention Meeting - {self.partner_id.name}',
                    'start': meeting_start,
                    'stop': meeting_end,
                    'partner_ids': [(4, self.partner_id.id)],
                    'description': f"""Retention meeting with {self.partner_id.name}

Risk Level: {self.risk_level}
Risk Score: {self.churn_risk_score}/100

Please discuss:
- Current concerns or issues
- Workload and scheduling
- Future collaboration plans
""",
                    'user_id': self.env.user.id,
                }

                # Add video call if available
                if hasattr(CalendarEvent, 'videocall_location'):
                    event_vals['videocall_location'] = 'meet'

                event = CalendarEvent.create(event_vals)

                self.message_post(
                    body=f"🤝 Created meeting: {event.name}",
                    message_type='notification',
                )

                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'calendar.event',
                    'res_id': event.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        except Exception:
            pass

        # Fallback: Open Google Calendar with pre-filled event
        import urllib.parse
        from datetime import datetime, timedelta

        meeting_start = datetime.now() + timedelta(days=1)
        meeting_start = meeting_start.replace(hour=10, minute=0, second=0, microsecond=0)
        meeting_end = meeting_start + timedelta(hours=1)

        # Format dates for Google Calendar
        start_str = meeting_start.strftime('%Y%m%dT%H%M%S')
        end_str = meeting_end.strftime('%Y%m%dT%H%M%S')

        title = urllib.parse.quote(f'GEP - Meeting with {self.partner_id.name}')
        details = urllib.parse.quote(f'Retention meeting to discuss collaboration.\n\nRisk Level: {self.risk_level}')
        guest_email = self.partner_email or ''

        google_cal_url = (
            f"https://calendar.google.com/calendar/render?action=TEMPLATE"
            f"&text={title}"
            f"&dates={start_str}/{end_str}"
            f"&details={details}"
            f"&add={guest_email}"
            f"&trp=false"
        )

        self.message_post(
            body=f"🤝 Opening Google Calendar to schedule meeting with {self.partner_id.name}",
            message_type='notification',
        )

        return {
            'type': 'ir.actions.act_url',
            'url': google_cal_url,
            'target': 'new',
        }

    def action_view_partner_visits(self):
        """View all visits assigned to this partner"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Visits - {self.partner_id.name}',
            'res_model': 'wfm.visit',
            'view_mode': 'list,kanban,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'search_default_upcoming': 1},
        }

    def _get_ai_suggestion(self):
        """
        Compute AI suggestion based on risk factors.
        Returns tuple: (suggested_action_key, reason_text)
        """
        # Analyze risk factors
        scores = {
            'decline': self.decline_rate_score or 0,
            'volume': self.volume_change_score or 0,
            'inactivity': self.inactivity_score or 0,
            'payment': self.payment_issue_score or 0,
            'feedback': self.feedback_score or 0,
        }

        dominant_factor = max(scores, key=scores.get) if any(scores.values()) else None

        if dominant_factor == 'decline' and scores['decline'] >= 15:
            return 'workload', (
                f"Partner declined {self.visits_declined_30d or 0} visits recently. "
                "They may be overwhelmed. Review and adjust their workload to better fit their availability."
            )
        elif dominant_factor == 'inactivity' and scores['inactivity'] >= 15:
            if self.days_since_last_visit and self.days_since_last_visit > 30:
                return 'meeting', (
                    f"Partner inactive for {self.days_since_last_visit} days. "
                    "An in-person meeting shows commitment and helps rebuild the relationship."
                )
            else:
                return 'call', "Early disengagement signs detected. A quick call can help understand issues before they escalate."
        elif dominant_factor == 'payment' and scores['payment'] >= 10:
            return 'bonus', (
                f"Partner has {self.payment_complaints or 0} payment-related complaints. "
                "Consider discussing compensation, offering a bonus, or reviewing payment terms."
            )
        elif dominant_factor == 'volume' and scores['volume'] >= 15:
            return 'call', "Visit volume dropped significantly. Call to understand if there are issues with assignments or personal circumstances."
        elif dominant_factor == 'feedback' and scores['feedback'] >= 5:
            return 'meeting', f"Partner received {self.negative_feedback_count or 0} negative feedback. Meet to discuss concerns and create improvement plan."
        elif self.risk_level == 'critical':
            return 'call', "CRITICAL risk level! Call the partner TODAY to understand their situation and prevent churn. Be prepared to offer solutions."
        elif self.risk_level == 'high':
            return 'whatsapp', "High risk level. Send a WhatsApp message - it's quick, personal, and opens the door for conversation."
        elif self.risk_level == 'medium':
            return 'email', "Medium risk. Send a friendly check-in email to maintain the relationship and show you value their partnership."
        else:
            return 'email', "Low risk - maintain relationship with periodic check-ins. A brief email keeps communication open."

    def action_show_ai_advice(self):
        """
        Show AI advice inline on the form by setting fields.
        No popup - the advice appears directly on the form.
        """
        self.ensure_one()

        suggested, reason = self._get_ai_suggestion()

        action_labels = {
            'call': '📞 Phone Call',
            'whatsapp': '💬 WhatsApp',
            'email': '📧 Email',
            'meeting': '🤝 In-Person Meeting',
            'bonus': '💰 Bonus/Incentive',
            'workload': '📊 Workload Adjustment',
        }

        # Set the planned action and AI advice text
        self.write({
            'planned_action': suggested,
            'ai_advice_text': f"💡 {action_labels.get(suggested, suggested)}: {reason}",
        })

        # Just reload the form - no popup
        return True

    def action_get_ai_suggestions(self):
        """Get AI-powered retention suggestions (on-demand only)"""
        self.ensure_one()

        # Use the AI Retention Engine
        try:
            engine = self.env['wfm.ai.retention.engine'].create({})
            result = engine.analyze_partner_and_generate_outreach(self.id)

            if result.get('success'):
                self.write({
                    'ai_analysis': result.get('analysis', ''),
                    'ai_whatsapp_message': result.get('whatsapp_message', ''),
                    'ai_recommended_action': result.get('recommended_action', ''),
                    'ai_urgency': result.get('urgency', 'monitor'),
                    'ai_generated_date': fields.Datetime.now(),
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '💡 AI Suggestions Ready',
                        'message': f'Strategy generated for {self.partner_id.name}',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'AI Suggestions Failed',
                        'message': result.get('error', 'Unknown error'),
                        'type': 'danger',
                        'sticky': True,
                    }
                }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'AI Suggestions Failed',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }


class WfmPartnerIntervention(models.Model):
    """
    Action Log for partner retention tickets.
    Each entry is a step taken by the coordinator.
    """
    _name = 'wfm.partner.intervention'
    _description = 'Partner Retention Action Log'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread']

    health_id = fields.Many2one(
        'wfm.partner.health',
        string='Ticket',
        required=True,
        ondelete='cascade'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        domain=[('is_wfm_partner', '=', True)]
    )
    date = fields.Datetime(
        string='Date & Time',
        default=fields.Datetime.now,
        required=True
    )
    coordinator_id = fields.Many2one(
        'res.users',
        string='Coordinator',
        default=lambda self: self.env.user,
        required=True
    )

    intervention_type = fields.Selection([
        ('call', '📞 Phone Call'),
        ('whatsapp', '💬 WhatsApp'),
        ('email', '📧 Email'),
        ('meeting', '🤝 In-Person Meeting'),
        ('bonus', '💰 Bonus/Incentive'),
        ('workload', '📊 Workload Adjustment'),
        ('note', '📝 Internal Note'),
    ], string='Action Type', required=True, default='call')

    # What happened
    summary = fields.Char(string='Summary', help='Brief description of what was done')
    notes = fields.Text(string='Details', help='Full notes about this action')

    # Partner's response
    partner_response = fields.Selection([
        ('no_answer', '📵 No Answer'),
        ('positive', '✅ Positive'),
        ('neutral', '😐 Neutral'),
        ('negative', '❌ Negative'),
        ('callback', '🔄 Will Call Back'),
    ], string='Partner Response')

    # Follow-up
    needs_follow_up = fields.Boolean(string='Needs Follow-up')
    follow_up_date = fields.Date(string='Follow-up Date')
    follow_up_notes = fields.Text(string='Follow-up Notes')

    # Legacy fields for backward compatibility
    risk_level_at_intervention = fields.Selection([
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🟠 High'),
        ('critical', '🔴 Critical'),
    ], string='Risk at Time', compute='_compute_risk_level_at_intervention', store=True, readonly=False)

    outcome = fields.Selection([
        ('pending', '⏳ Pending'),
        ('positive', '✅ Positive Response'),
        ('neutral', '➡️ Neutral'),
        ('negative', '❌ Negative Response'),
        ('retained', '🎉 Partner Retained'),
        ('churned', '💔 Partner Left'),
    ], string='Outcome', compute='_compute_outcome', store=True, readonly=False)

    # AI Suggestions (computed only, not stored)
    suggested_action = fields.Char(string='Suggested Action', compute='_compute_suggestions')
    suggestion_reason = fields.Text(string='Why This Approach', compute='_compute_suggestions')

    @api.depends('health_id')
    def _compute_risk_level_at_intervention(self):
        """Auto-set risk level from health record"""
        for record in self:
            if record.health_id and not record.risk_level_at_intervention:
                record.risk_level_at_intervention = record.health_id.risk_level
            elif not record.risk_level_at_intervention:
                record.risk_level_at_intervention = False

    @api.depends('partner_response')
    def _compute_outcome(self):
        """Map partner response to legacy outcome field"""
        response_to_outcome = {
            'positive': 'positive',
            'neutral': 'neutral',
            'negative': 'negative',
            'no_answer': 'pending',
            'callback': 'pending',
        }
        for record in self:
            if record.partner_response:
                record.outcome = response_to_outcome.get(record.partner_response, 'pending')
            else:
                record.outcome = 'pending'

    @api.depends('health_id')
    def _compute_suggestions(self):
        """AI-powered intervention suggestions based on risk factors"""
        suggestions_map = {
            'call': '📞 Phone Call',
            'meeting': '🤝 Meeting',
            'email': '📧 Email',
            'bonus': '💰 Bonus/Incentive',
            'training': '📚 Training Offer',
            'workload': '📊 Workload Adjustment',
        }

        for record in self:
            suggested_key = 'call'
            reason = 'Start with a phone call to understand the situation.'

            if record.health_id:
                health = record.health_id

                # Analyze risk factors to suggest best intervention
                if health.decline_rate_score >= 20:
                    suggested_key = 'workload'
                    reason = (
                        f"Partner declined {health.visits_declined_30d} visits recently. "
                        "Consider adjusting workload or discussing scheduling conflicts."
                    )
                elif health.inactivity_score >= 15:
                    suggested_key = 'meeting'
                    reason = (
                        f"Partner inactive for {health.days_since_last_visit} days. "
                        "A face-to-face meeting shows commitment and helps understand concerns."
                    )
                elif health.payment_issue_score >= 10:
                    suggested_key = 'bonus'
                    reason = (
                        "Payment complaints detected. Consider offering a bonus or "
                        "reviewing payment terms to address financial concerns."
                    )
                elif health.volume_change_score >= 15:
                    suggested_key = 'training'
                    reason = (
                        "Visit volume dropped significantly. Offer training or "
                        "certifications to increase engagement and opportunities."
                    )
                elif health.risk_level == 'critical':
                    suggested_key = 'call'
                    reason = (
                        "Critical risk level requires immediate outreach. "
                        "Call to understand concerns before they leave."
                    )
                else:
                    suggested_key = 'email'
                    reason = (
                        "Send a check-in email to maintain relationship "
                        "and gather feedback on their experience."
                    )

            record.suggested_action = suggestions_map.get(suggested_key, '📞 Phone Call')
            record.suggestion_reason = reason

    @api.model_create_multi
    def create(self, vals_list):
        """Update ticket to in_progress when first action is logged"""
        records = super().create(vals_list)
        for record in records:
            if record.health_id and record.health_id.ticket_state == 'open':
                record.health_id.write({'ticket_state': 'in_progress'})
        return records

    def action_view_ticket(self):
        """Navigate to the parent ticket"""
        self.ensure_one()
        if self.health_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'wfm.partner.health',
                'res_id': self.health_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {'type': 'ir.actions.act_window_close'}
