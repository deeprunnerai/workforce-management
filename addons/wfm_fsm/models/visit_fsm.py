from odoo import models, fields, api, _


class WfmVisitFsm(models.Model):
    """Extend wfm.visit with FSM-specific fields and stage/state sync."""
    _inherit = 'wfm.visit'

    # Coordinator assigned to manage this visit
    coordinator_id = fields.Many2one(
        'res.users',
        string='Coordinator',
        default=lambda self: self.env.user,
        tracking=True
    )

    # Overdue flag
    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_is_overdue',
        store=True
    )

    # Recommended partners (computed for form view)
    recommended_partner_ids = fields.Many2many(
        'res.partner',
        string='Recommended Partners',
        compute='_compute_recommended_partners'
    )
    recommendation_html = fields.Html(
        string='Partner Recommendations',
        compute='_compute_recommended_partners',
        sanitize=False
    )

    # AI recommendation cache
    ai_recommendation = fields.Text(
        string='AI Recommendation',
        help='Cached AI recommendation from Claude'
    )
    ai_recommendation_html = fields.Html(
        string='AI Recommendation Display',
        help='HTML display of AI recommendation',
        sanitize=False
    )

    @api.depends('client_id', 'installation_id', 'visit_date')
    def _compute_recommended_partners(self):
        """Compute recommended partners using assignment engine."""
        engine = self.env['wfm.assignment.engine']
        for visit in self:
            if visit.id and visit.client_id:
                try:
                    recommendations = engine.get_recommended_partners(visit.id, limit=5)
                    partner_ids = [r['partner_id'] for r in recommendations[:2]]
                    visit.recommended_partner_ids = [(6, 0, partner_ids)]

                    if recommendations:
                        visit.recommendation_html = self._build_recommendation_table(recommendations[:2])
                    else:
                        visit.recommendation_html = '<p class="text-muted">No recommendations available</p>'
                except Exception:
                    visit.recommended_partner_ids = [(5, 0, 0)]
                    visit.recommendation_html = '<p class="text-muted">Unable to calculate recommendations</p>'
            else:
                visit.recommended_partner_ids = [(5, 0, 0)]
                visit.recommendation_html = '<p class="text-muted">Save visit to see recommendations</p>'

    def action_get_ai_recommendation(self):
        """Get AI-powered recommendation from Claude."""
        self.ensure_one()

        # Get rule-based candidates first
        engine = self.env['wfm.assignment.engine']
        candidates = engine.get_recommended_partners(self.id, limit=5)

        if not candidates:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Candidates',
                    'message': 'No available partners found for this visit',
                    'type': 'warning',
                }
            }

        # Get AI analysis
        ai_engine = self.env['wfm.ai.retention.engine'].create({})
        result = ai_engine.get_ai_partner_recommendation(self.id, candidates)

        if result.get('success'):
            # Build AI recommendation HTML
            confidence = result.get('confidence', 'medium')
            confidence_color = {
                'high': 'success',
                'medium': 'warning',
                'low': 'danger'
            }.get(confidence, 'secondary')

            recommended_partner = result.get('recommended_partner', 'Unknown')
            reasoning = result.get('reasoning', 'No reasoning provided')
            concerns = result.get('concerns')
            summary = result.get('summary', reasoning)

            ai_html = f'''
            <div class="alert alert-{confidence_color} mb-3" style="border-left: 4px solid;">
                <div class="d-flex align-items-center mb-2">
                    <span class="h4 mb-0 me-2">🤖</span>
                    <strong class="h5 mb-0">AI Recommends: {recommended_partner}</strong>
                    <span class="badge bg-{confidence_color} ms-2">{confidence.upper()}</span>
                </div>
                <p class="mb-2" style="font-size: 14px;">{reasoning}</p>
                {f'<div class="alert alert-light py-2 px-3 mb-0"><strong>⚠️ Note:</strong> {concerns}</div>' if concerns else ''}
            </div>
            '''

            # Store AI recommendation in stored field
            self.write({
                'ai_recommendation': summary,
                'ai_recommendation_html': ai_html
            })

            # Return action to reload the form to show updated AI HTML
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'wfm.visit',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'AI Analysis Failed',
                    'message': result.get('error', 'Unknown error'),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def _get_health_status(self, partner_id):
        """Get health status for a partner (if any concerns exist).

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
            reason = f"declined {health.visits_declined_30d} visits"
        elif health.inactivity_score >= 10:
            days = health.days_since_last_visit
            if days >= 60:
                reason = "long inactive"
            else:
                reason = f"inactive {days}d"
        elif health.volume_change_score >= 15:
            reason = "activity drop"
        elif health.payment_issue_score >= 5:
            reason = "payment issue"
        else:
            reason = "needs attention"

        return f'{risk_emoji} {risk_label}: {reason}'

    def _build_recommendation_table(self, recommendations):
        """Build a clear table showing partner recommendations with AI reasoning."""
        # Check if any partner has relationship history
        has_relationship = any(rec.get('relationship_score', 0) > 0 for rec in recommendations)
        top_score = recommendations[0]['total_score'] if recommendations else 0

        html = ''

        # Add context message based on scores
        if not has_relationship:
            html += '''
            <div class="alert alert-info py-2 mb-2" style="font-size: 13px;">
                <strong>Note:</strong> No partner has visited this client before.
                Recommendations are based on availability, performance, proximity & workload.
                After visits are completed, relationship data will improve future recommendations.
            </div>
            '''
        elif top_score >= 70:
            html += '''
            <div class="alert alert-success py-2 mb-2" style="font-size: 13px;">
                <strong>Great match!</strong> Top partner has strong relationship with this client.
            </div>
            '''

        html += '''
        <table class="table table-sm table-bordered mb-2" style="font-size: 13px;">
            <thead class="table-light">
                <tr>
                    <th style="width: 5%;">#</th>
                    <th style="width: 25%;">Partner</th>
                    <th style="width: 10%;">Score</th>
                    <th style="width: 45%;">Why Recommended</th>
                    <th style="width: 15%;">Health</th>
                </tr>
            </thead>
            <tbody>
        '''

        for i, rec in enumerate(recommendations, 1):
            rel_score = rec.get('relationship_score', 0)
            avail_score = rec.get('availability_score', 0)
            perf_score = rec.get('performance_score', 0)
            prox_score = rec.get('proximity_score', 0)
            work_score = rec.get('workload_score', 0)

            # Build clear reason
            reasons = []

            # Relationship (35%)
            if rel_score >= 25:
                reasons.append(f"<b>Strong relationship</b> ({rec.get('relationship_details', '')})")
            elif rel_score >= 15:
                reasons.append(f"Has history ({rec.get('relationship_details', '')})")
            elif rel_score > 0:
                reasons.append(f"Some history ({rec.get('relationship_details', '')})")
            # Don't show "New to client" - already covered by alert

            # Availability (25%)
            if avail_score >= 20:
                reasons.append("Fully available")
            elif avail_score >= 15:
                reasons.append("Available")
            else:
                reasons.append("<span class='text-warning'>Limited availability</span>")

            # Performance (20%)
            if perf_score >= 15:
                reasons.append("Great track record")
            elif perf_score >= 10:
                reasons.append("Good performance")

            # Proximity (10%)
            if prox_score >= 8:
                reasons.append("Same city")
            elif prox_score >= 5:
                reasons.append("Nearby")

            # Workload (10%)
            if work_score >= 8:
                reasons.append("Light workload")

            # Style based on rank
            row_class = 'table-success' if i == 1 else ''
            rank_badge = 'bg-success' if i == 1 else 'bg-info'

            # Get health status for this partner
            health_note = self._get_health_status(rec['partner_id'])
            if not health_note:
                health_note = '<span class="text-success">✓ Good</span>'

            html += f'''
                <tr class="{row_class}">
                    <td><span class="badge {rank_badge}">{i}</span></td>
                    <td><strong>{rec['partner_name']}</strong></td>
                    <td><strong>{rec['total_score']:.0f}</strong>/100</td>
                    <td>{" • ".join(reasons) if reasons else "Best available option"}</td>
                    <td style="font-size: 11px;">{health_note}</td>
                </tr>
            '''

        html += '''
            </tbody>
        </table>
        <div class="small text-muted">
            <b>Scoring:</b> Relationship 35% • Availability 25% • Performance 20% • Proximity 10% • Workload 10%
        </div>
        '''
        return html

    @api.depends('visit_date', 'state')
    def _compute_is_overdue(self):
        """Check if visit is overdue (past date and not completed)."""
        today = fields.Date.context_today(self)
        for visit in self:
            visit.is_overdue = (
                visit.visit_date
                and visit.visit_date < today
                and visit.state not in ('done', 'cancelled')
            )

    def _get_stage_for_state(self, state):
        """Get the stage_id that corresponds to a state."""
        state_to_stage = {
            'draft': 'Draft',
            'assigned': 'Assigned',
            'confirmed': 'Confirmed',
            'in_progress': 'In Progress',
            'done': 'Completed',
        }
        stage_name = state_to_stage.get(state)
        if stage_name:
            stage = self.env['wfm.visit.stage'].search([('name', 'ilike', stage_name)], limit=1)
            return stage.id if stage else False
        return False

    def _get_state_for_stage(self, stage_id):
        """Get the state that corresponds to a stage_id."""
        if not stage_id:
            return False
        stage = self.env['wfm.visit.stage'].browse(stage_id)
        stage_name = stage.name
        if isinstance(stage_name, dict):
            stage_name = stage_name.get('en_US', list(stage_name.values())[0])

        stage_to_state = {
            'Draft': 'draft',
            'Assigned': 'assigned',
            'Confirmed': 'confirmed',
            'In Progress': 'in_progress',
            'Completed': 'done',
        }
        return stage_to_state.get(stage_name)

    def write(self, vals):
        """Sync state and stage_id when either changes."""
        # If state is changing, also update stage_id
        if 'state' in vals and 'stage_id' not in vals:
            stage_id = self._get_stage_for_state(vals['state'])
            if stage_id:
                vals['stage_id'] = stage_id

        # If stage_id is changing (drag-drop), also update state
        if 'stage_id' in vals and 'state' not in vals:
            new_state = self._get_state_for_stage(vals['stage_id'])
            if new_state:
                vals['state'] = new_state

        return super().write(vals)

    # Override action methods to ensure stage syncs with state
    def action_assign(self):
        """Assign the visit."""
        stage_id = self._get_stage_for_state('assigned')
        self.write({'state': 'assigned', 'stage_id': stage_id})

    def action_confirm(self):
        """Confirm the visit."""
        stage_id = self._get_stage_for_state('confirmed')
        self.write({'state': 'confirmed', 'stage_id': stage_id})

    def action_start(self):
        """Start the visit."""
        stage_id = self._get_stage_for_state('in_progress')
        self.write({'state': 'in_progress', 'stage_id': stage_id})

    def action_complete(self):
        """Complete the visit and update partner-client relationship."""
        stage_id = self._get_stage_for_state('done')
        self.write({'state': 'done', 'stage_id': stage_id})

        # Update partner-client relationship for completed visits
        self._update_partner_relationship()

    def _update_partner_relationship(self):
        """Update partner-client relationship metrics after visit completion."""
        Relationship = self.env['wfm.partner.client.relationship']
        for visit in self:
            if visit.partner_id and visit.client_id and visit.state == 'done':
                relationship = Relationship.get_or_create_relationship(
                    visit.partner_id.id,
                    visit.client_id.id
                )
                relationship.update_from_visit(visit, is_completion=True)

    def action_cancel(self):
        """Cancel the visit."""
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """Reset to draft state."""
        stage_id = self._get_stage_for_state('draft')
        self.write({'state': 'draft', 'stage_id': stage_id})

    @api.model
    def get_dashboard_data(self):
        """Get counts for dashboard cards."""
        today = fields.Date.context_today(self)
        domain = [('active', '=', True)]

        return {
            'green': self.search_count(domain + [('state', '=', 'done')]),
            'yellow': self.search_count(domain + [
                ('state', 'in', ('assigned', 'confirmed')),
                ('visit_date', '>=', today)
            ]),
            'orange': self.search_count(domain + [('state', '=', 'in_progress')]),
            'red': self.search_count(domain + [
                ('state', 'not in', ('done', 'cancelled')),
                ('visit_date', '<', today)
            ]),
            'total': self.search_count(domain),
            'today': self.search_count(domain + [('visit_date', '=', today)]),
            'unassigned': self.search_count(domain + [
                ('state', '=', 'draft'),
                ('partner_id', '=', False)
            ]),
            'this_week': self.search_count(domain + [
                ('visit_date', '>=', today),
                ('visit_date', '<=', fields.Date.add(today, days=7))
            ]),
        }

    @api.model
    def get_visits_action(self, filter_type):
        """Return action to view filtered visits."""
        today = fields.Date.context_today(self)
        domain = [('active', '=', True)]

        if filter_type == 'green':
            domain += [('state', '=', 'done')]
            name = 'Completed Visits'
        elif filter_type == 'yellow':
            domain += [('state', 'in', ('assigned', 'confirmed')), ('visit_date', '>=', today)]
            name = 'Upcoming Visits'
        elif filter_type == 'orange':
            domain += [('state', '=', 'in_progress')]
            name = 'In Progress'
        elif filter_type == 'red':
            domain += [('state', 'not in', ('done', 'cancelled')), ('visit_date', '<', today)]
            name = 'Overdue Visits'
        elif filter_type == 'today':
            domain += [('visit_date', '=', today)]
            name = "Today's Visits"
        elif filter_type == 'unassigned':
            domain += [('state', '=', 'draft'), ('partner_id', '=', False)]
            name = 'Unassigned Visits'
        else:
            name = 'Visits'

        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'wfm.visit',
            'view_mode': 'kanban,list,form',
            'views': [
                [False, 'kanban'],
                [False, 'list'],
                [False, 'form'],
            ],
            'domain': domain,
            'context': {'search_default_group_by_stage': 1},
            'target': 'current',
        }

    def action_open_smart_assign(self):
        """Open the Smart Assignment Wizard."""
        self.ensure_one()
        return {
            'name': _('Smart Partner Assignment'),
            'type': 'ir.actions.act_window',
            'res_model': 'wfm.smart.assign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_visit_id': self.id},
        }
