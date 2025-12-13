from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WfmSmartAssignWizard(models.TransientModel):
    """Smart Assignment Wizard with AI-powered partner recommendations.

    Shows Top 2 recommended partners based on:
    - Relationship (35%): Prior visit history
    - Availability (25%): Schedule conflicts
    - Performance (20%): Completion rate, ratings
    - Proximity (10%): Geographic location
    - Workload (10%): Current assignment balance
    """
    _name = 'wfm.smart.assign.wizard'
    _description = 'Smart Partner Assignment Wizard'

    # Visit being assigned
    visit_id = fields.Many2one(
        'wfm.visit',
        string='Visit',
        required=True,
        default=lambda self: self._default_visit_id(),
        readonly=True
    )

    # Visit info (readonly display)
    client_id = fields.Many2one(
        related='visit_id.client_id',
        string='Client',
        readonly=True
    )
    installation_id = fields.Many2one(
        related='visit_id.installation_id',
        string='Installation',
        readonly=True
    )
    visit_date = fields.Date(
        related='visit_id.visit_date',
        string='Visit Date',
        readonly=True
    )

    # Partner selection
    partner_id = fields.Many2one(
        'res.partner',
        string='Assign Partner',
        domain=[('is_wfm_partner', '=', True)]
    )

    # Top 2 Recommendations
    recommendation_1_id = fields.Many2one(
        'res.partner',
        string='Top Recommendation',
        compute='_compute_recommendations',
        readonly=True
    )
    recommendation_1_score = fields.Float(
        string='Score #1',
        compute='_compute_recommendations'
    )
    recommendation_1_details = fields.Char(
        string='Details #1',
        compute='_compute_recommendations'
    )

    recommendation_2_id = fields.Many2one(
        'res.partner',
        string='Second Recommendation',
        compute='_compute_recommendations',
        readonly=True
    )
    recommendation_2_score = fields.Float(
        string='Score #2',
        compute='_compute_recommendations'
    )
    recommendation_2_details = fields.Char(
        string='Details #2',
        compute='_compute_recommendations'
    )

    # Full recommendation data (for display)
    recommendations_html = fields.Html(
        string='Recommendations',
        compute='_compute_recommendations',
        sanitize=False
    )

    # AI recommendation fields
    ai_recommended_partner_id = fields.Many2one(
        'res.partner',
        string='AI Recommended Partner',
        help='Partner recommended by Claude AI'
    )
    ai_recommendation_html = fields.Html(
        string='AI Recommendation',
        sanitize=False
    )
    ai_confidence = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string='AI Confidence')

    def _default_visit_id(self):
        """Get visit from context."""
        active_id = self.env.context.get('active_id')
        if active_id:
            return active_id
        return False

    @api.depends('visit_id')
    def _compute_recommendations(self):
        """Compute top 2 partner recommendations."""
        engine = self.env['wfm.assignment.engine']

        for wizard in self:
            # Reset values
            wizard.recommendation_1_id = False
            wizard.recommendation_1_score = 0
            wizard.recommendation_1_details = ''
            wizard.recommendation_2_id = False
            wizard.recommendation_2_score = 0
            wizard.recommendation_2_details = ''
            wizard.recommendations_html = ''

            if not wizard.visit_id:
                wizard.recommendations_html = '<p class="text-muted">No visit selected</p>'
                continue

            try:
                recommendations = engine.get_recommended_partners(wizard.visit_id.id, limit=2)

                if len(recommendations) >= 1:
                    rec1 = recommendations[0]
                    wizard.recommendation_1_id = rec1['partner_id']
                    wizard.recommendation_1_score = rec1['total_score']
                    wizard.recommendation_1_details = f"{rec1.get('relationship_details', '')} | {rec1.get('availability_details', '')}"

                if len(recommendations) >= 2:
                    rec2 = recommendations[1]
                    wizard.recommendation_2_id = rec2['partner_id']
                    wizard.recommendation_2_score = rec2['total_score']
                    wizard.recommendation_2_details = f"{rec2.get('relationship_details', '')} | {rec2.get('availability_details', '')}"

                # Build HTML display
                wizard.recommendations_html = wizard._build_recommendations_html(recommendations)

            except Exception as e:
                wizard.recommendations_html = f'<p class="text-danger">Error: {str(e)}</p>'

    def _build_recommendations_html(self, recommendations):
        """Build HTML display for recommendations with AI reasoning."""
        if not recommendations:
            return '<p class="text-warning">No partners available for recommendation</p>'

        html = '<div class="o_smart_recommendations">'

        for i, rec in enumerate(recommendations, 1):
            score = rec['total_score']

            # Score breakdown
            rel_score = rec.get('relationship_score', 0)
            avail_score = rec.get('availability_score', 0)
            perf_score = rec.get('performance_score', 0)
            prox_score = rec.get('proximity_score', 0)
            work_score = rec.get('workload_score', 0)

            # Build AI reasoning - why this partner is recommended
            reasons = []

            # Relationship (35% weight - TOP PRIORITY)
            if rel_score >= 25:
                reasons.append(f"Strong client relationship ({rec.get('relationship_details', '')})")
            elif rel_score >= 15:
                reasons.append(f"Has worked with client ({rec.get('relationship_details', '')})")
            elif rel_score == 0:
                reasons.append("New to this client")

            # Availability (25% weight)
            if avail_score >= 20:
                reasons.append("Fully available")
            elif avail_score >= 15:
                reasons.append("Good availability")
            elif avail_score < 10:
                reasons.append("Limited availability")

            # Performance (20% weight)
            if perf_score >= 15:
                reasons.append("Excellent track record")
            elif perf_score >= 10:
                reasons.append("Good performance")

            # Proximity (10% weight)
            if prox_score >= 8:
                reasons.append("Same city")
            elif prox_score >= 5:
                reasons.append("Nearby location")

            # Workload (10% weight)
            if work_score >= 8:
                reasons.append("Light workload")
            elif work_score < 5:
                reasons.append("Heavy workload")

            # Get health status one-liner (if any concerns)
            health_alert = self._get_health_alert(rec['partner_id'])

            # Determine card style based on rank
            if i == 1:
                border_color = 'success'
                header_bg = 'bg-success text-white'
                rank_label = 'TOP PICK'
            else:
                border_color = 'info'
                header_bg = 'bg-info text-white'
                rank_label = 'ALTERNATIVE'

            # Build reason summary (one line)
            reason_text = ' | '.join(reasons[:3])  # Show top 3 reasons

            html += f'''
            <div class="card mb-3 border-{border_color}" style="border-width: 2px;">
                <div class="card-header {header_bg} py-2">
                    <div class="d-flex justify-content-between align-items-center">
                        <span>
                            <span class="badge bg-light text-dark me-2">#{i}</span>
                            <strong>{rec['partner_name']}</strong>
                            <small class="ms-2 opacity-75">({rec.get('partner_specialty', 'N/A') or 'N/A'})</small>
                        </span>
                        <span class="badge bg-light text-dark fs-6">{score:.0f}/100</span>
                    </div>
                </div>
                <div class="card-body py-2">
                    <!-- Health Alert (if any) -->
                    {health_alert}

                    <!-- AI Reasoning Summary -->
                    <div class="alert alert-light py-1 px-2 mb-2 small">
                        <strong>Why recommended:</strong> {reason_text}
                    </div>

                    <!-- Score Breakdown with Icons -->
                    <div class="row small text-center">
                        <div class="col" title="Client Relationship (35%) - TOP PRIORITY">
                            <div class="fw-bold text-{"success" if rel_score >= 20 else "secondary"}">{rel_score:.0f}/35</div>
                            <div class="text-muted small">Relationship</div>
                        </div>
                        <div class="col" title="Availability (25%)">
                            <div class="fw-bold text-{"success" if avail_score >= 20 else "warning" if avail_score >= 10 else "danger"}">{avail_score:.0f}/25</div>
                            <div class="text-muted small">Availability</div>
                        </div>
                        <div class="col" title="Performance (20%)">
                            <div class="fw-bold text-{"success" if perf_score >= 15 else "secondary"}">{perf_score:.0f}/20</div>
                            <div class="text-muted small">Performance</div>
                        </div>
                        <div class="col" title="Proximity (10%)">
                            <div class="fw-bold">{prox_score:.0f}/10</div>
                            <div class="text-muted small">Proximity</div>
                        </div>
                        <div class="col" title="Workload Balance (10%)">
                            <div class="fw-bold">{work_score:.0f}/10</div>
                            <div class="text-muted small">Workload</div>
                        </div>
                    </div>
                </div>
            </div>
            '''

        # Add legend
        html += '''
        <div class="small text-muted mt-2 p-2 bg-light rounded">
            <strong>Scoring Weights:</strong>
            Client Relationship (35%) |
            Availability (25%) |
            Performance (20%) |
            Proximity (10%) |
            Workload (10%)
        </div>
        '''

        html += '</div>'
        return html

    def action_get_ai_recommendation(self):
        """Get AI-powered recommendation from Claude."""
        self.ensure_one()

        if not self.visit_id:
            raise UserError(_('No visit selected.'))

        # Get rule-based candidates first
        engine = self.env['wfm.assignment.engine']
        candidates = engine.get_recommended_partners(self.visit_id.id, limit=5)

        if not candidates:
            raise UserError(_('No available partners found for this visit.'))

        # Get AI analysis from Claude
        ai_engine = self.env['wfm.ai.retention.engine'].create({})
        result = ai_engine.get_ai_partner_recommendation(self.visit_id.id, candidates)

        if result.get('success'):
            # Find the recommended partner by name
            recommended_name = result.get('recommended_partner', '')
            recommended_partner = None

            for c in candidates:
                if c['partner_name'] == recommended_name:
                    recommended_partner = self.env['res.partner'].browse(c['partner_id'])
                    break

            # If not found by exact name, use the first candidate
            if not recommended_partner:
                recommended_partner = self.env['res.partner'].browse(candidates[0]['partner_id'])

            confidence = result.get('confidence', 'medium')
            confidence_color = {
                'high': 'success',
                'medium': 'warning',
                'low': 'danger'
            }.get(confidence, 'secondary')

            # Get reasoning - check multiple possible keys
            reasoning = result.get('reasoning') or result.get('summary') or result.get('raw_response', '')
            if not reasoning or reasoning == 'No reasoning provided':
                # Build reasoning from candidate data
                for c in candidates:
                    if c['partner_name'] == recommended_name or c['partner_id'] == recommended_partner.id:
                        reasons = []
                        if c.get('relationship_score', 0) > 0:
                            reasons.append(f"Has history with client ({c.get('relationship_details', '')})")
                        if c.get('availability_score', 0) >= 20:
                            reasons.append("Fully available")
                        if c.get('performance_score', 0) >= 15:
                            reasons.append("Strong performance record")
                        if c.get('proximity_score', 0) >= 8:
                            reasons.append("Same city location")
                        reasoning = '. '.join(reasons) if reasons else f"Best available match with score {c['total_score']}/100"
                        break

            concerns = result.get('concerns')

            ai_html = f'''
            <div class="alert alert-{confidence_color} mb-3" style="border-left: 4px solid;">
                <div class="d-flex align-items-center mb-2">
                    <span class="h4 mb-0 me-2">🤖</span>
                    <strong class="h5 mb-0">AI Recommends: {recommended_partner.name}</strong>
                    <span class="badge bg-{confidence_color} ms-2">{confidence.upper()}</span>
                </div>
                <p class="mb-2" style="font-size: 14px;">{reasoning}</p>
                {f'<div class="alert alert-light py-2 px-3 mb-0"><strong>⚠️ Note:</strong> {concerns}</div>' if concerns else ''}
            </div>
            '''

            self.write({
                'ai_recommended_partner_id': recommended_partner.id,
                'ai_recommendation_html': ai_html,
                'ai_confidence': confidence,
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '🤖 AI Analysis Complete',
                    'message': f'Claude recommends: {recommended_partner.name}',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError(_(f'AI Analysis Failed: {result.get("error", "Unknown error")}'))

    def action_assign_ai_recommendation(self):
        """Assign the AI-recommended partner."""
        self.ensure_one()
        if not self.ai_recommended_partner_id:
            raise UserError(_('No AI recommendation available. Click "Ask AI" first.'))
        return self._assign_partner(self.ai_recommended_partner_id)

    def action_assign_recommendation_1(self):
        """Assign the top recommended partner."""
        self.ensure_one()
        if not self.recommendation_1_id:
            raise UserError(_('No recommendation available.'))
        return self._assign_partner(self.recommendation_1_id)

    def action_assign_recommendation_2(self):
        """Assign the second recommended partner."""
        self.ensure_one()
        if not self.recommendation_2_id:
            raise UserError(_('No second recommendation available.'))
        return self._assign_partner(self.recommendation_2_id)

    def action_assign_selected(self):
        """Assign the manually selected partner."""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_('Please select a partner to assign.'))
        return self._assign_partner(self.partner_id)

    def _assign_partner(self, partner):
        """Assign partner to visit and close wizard."""
        self.ensure_one()
        engine = self.env['wfm.assignment.engine']

        # Use engine to assign (handles state change)
        engine.assign_partner_to_visit(self.visit_id.id, partner.id)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Partner Assigned'),
                'message': _('%(partner)s has been assigned to visit %(visit)s',
                           partner=partner.name, visit=self.visit_id.name),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _get_health_alert(self, partner_id):
        """Get health alert for a partner (if any concerns exist).

        This doesn't affect the scoring, just provides coordinator awareness.

        Returns:
            HTML string with alert (or empty string if healthy)
        """
        # Look for any open/in_progress health tickets for this partner
        health = self.env['wfm.partner.health'].search([
            ('partner_id', '=', partner_id),
            ('ticket_state', 'in', ['open', 'in_progress']),
            ('risk_level', 'in', ['high', 'critical']),
        ], order='churn_risk_score desc', limit=1)

        if not health:
            return ''

        # Build one-liner based on risk level
        if health.risk_level == 'critical':
            risk_emoji = '🔴'
            risk_label = 'At Risk'
        else:
            risk_emoji = '🟠'
            risk_label = 'Watch'

        # Build reason based on highest score component
        reason = ''
        if health.decline_rate_score >= 15:
            reason = f"declined {health.visits_declined_30d} recent visits"
        elif health.inactivity_score >= 10:
            days = health.days_since_last_visit
            if days >= 60:
                reason = "long inactive"
            else:
                reason = f"inactive for {days} days"
        elif health.volume_change_score >= 15:
            reason = "drop in activity"
        elif health.payment_issue_score >= 5:
            reason = "payment concerns"
        else:
            reason = "needs attention"

        # Build the alert HTML - informational only, not blocking
        alert_html = f'''
        <div class="alert alert-warning py-1 px-2 mb-2 small d-flex align-items-center">
            <span class="me-2">{risk_emoji}</span>
            <span><strong>{risk_label}:</strong> {reason}
            <em class="text-muted ms-1">(FYI only - doesn't affect score)</em></span>
        </div>
        '''

        return alert_html
