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
