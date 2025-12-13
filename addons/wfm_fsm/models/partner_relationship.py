from odoo import models, fields, api
from odoo.models import Constraint


class WfmPartnerClientRelationship(models.Model):
    """Track relationship history between partners and clients.

    This model stores aggregated visit history to enable relationship-based
    partner recommendations. Key insight: Clients prefer partners who know
    their facility (relationship continuity > proximity).
    """
    _name = 'wfm.partner.client.relationship'
    _description = 'Partner-Client Relationship'
    _order = 'total_visits desc'
    _rec_name = 'partner_id'

    # Core relations
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        domain=[('is_wfm_partner', '=', True)],
        ondelete='cascade',
        index=True
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
        required=True,
        domain=[('is_wfm_client', '=', True)],
        ondelete='cascade',
        index=True
    )

    # Visit statistics
    total_visits = fields.Integer(
        string='Total Visits',
        default=0,
        help='Total number of completed visits by this partner for this client'
    )
    completed_visits = fields.Integer(
        string='Completed Visits',
        default=0,
        help='Number of successfully completed visits'
    )
    cancelled_visits = fields.Integer(
        string='Cancelled Visits',
        default=0,
        help='Number of cancelled visits'
    )

    # Performance metrics
    avg_rating = fields.Float(
        string='Average Rating',
        digits=(3, 2),
        default=0.0,
        help='Average client satisfaction rating (1-5)'
    )
    on_time_rate = fields.Float(
        string='On-Time Rate (%)',
        digits=(5, 2),
        default=100.0,
        help='Percentage of visits completed on schedule'
    )

    # Timeline
    first_visit_date = fields.Date(
        string='First Visit',
        help='Date of first visit by this partner to this client'
    )
    last_visit_date = fields.Date(
        string='Last Visit',
        help='Date of most recent visit'
    )

    # Relationship strength (computed)
    relationship_score = fields.Float(
        string='Relationship Score',
        compute='_compute_relationship_score',
        store=True,
        help='Calculated relationship strength (0-100)'
    )

    # Installation familiarity
    installations_visited = fields.Integer(
        string='Installations Visited',
        default=0,
        help='Number of unique installations visited for this client'
    )

    _partner_client_unique = Constraint(
        'UNIQUE(partner_id, client_id)',
        'A relationship record already exists for this partner-client pair.'
    )

    @api.depends('total_visits', 'completed_visits', 'avg_rating', 'on_time_rate', 'last_visit_date')
    def _compute_relationship_score(self):
        """Calculate relationship strength score (0-100).

        Scoring factors:
        - Visit count: More visits = stronger relationship (40%)
        - Completion rate: Higher completion = more reliable (20%)
        - Rating: Client satisfaction (20%)
        - Recency: Recent visits weighted higher (20%)
        """
        today = fields.Date.context_today(self)
        for rel in self:
            score = 0.0

            # Visit count factor (0-40 points)
            # Cap at 20 visits for max score
            visit_score = min(rel.total_visits / 20.0, 1.0) * 40
            score += visit_score

            # Completion rate factor (0-20 points)
            if rel.total_visits > 0:
                completion_rate = rel.completed_visits / rel.total_visits
                score += completion_rate * 20

            # Rating factor (0-20 points)
            # Rating is 1-5, normalize to 0-1
            if rel.avg_rating > 0:
                rating_score = (rel.avg_rating - 1) / 4.0 * 20
                score += rating_score

            # Recency factor (0-20 points)
            # Full points if visited within 30 days, decreasing over 180 days
            if rel.last_visit_date:
                days_since = (today - rel.last_visit_date).days
                if days_since <= 30:
                    recency_score = 20
                elif days_since <= 180:
                    recency_score = 20 * (1 - (days_since - 30) / 150.0)
                else:
                    recency_score = 0
                score += max(recency_score, 0)

            rel.relationship_score = min(score, 100)

    @api.model
    def get_or_create_relationship(self, partner_id, client_id):
        """Get existing relationship or create new one."""
        relationship = self.search([
            ('partner_id', '=', partner_id),
            ('client_id', '=', client_id)
        ], limit=1)

        if not relationship:
            relationship = self.create({
                'partner_id': partner_id,
                'client_id': client_id,
            })

        return relationship

    def update_from_visit(self, visit, is_completion=False):
        """Update relationship metrics after a visit.

        Args:
            visit: wfm.visit record
            is_completion: True if visit was just completed
        """
        self.ensure_one()
        vals = {}

        if is_completion:
            vals['completed_visits'] = self.completed_visits + 1
            vals['total_visits'] = self.total_visits + 1
            vals['last_visit_date'] = visit.visit_date

            if not self.first_visit_date:
                vals['first_visit_date'] = visit.visit_date

            # Track unique installations
            visited_installations = self.env['wfm.visit'].search([
                ('partner_id', '=', self.partner_id.id),
                ('client_id', '=', self.client_id.id),
                ('state', '=', 'done')
            ]).mapped('installation_id')
            vals['installations_visited'] = len(visited_installations)

        if vals:
            self.write(vals)

    def action_view_visits(self):
        """View all visits for this partner-client relationship."""
        self.ensure_one()
        return {
            'name': f'Visits: {self.partner_id.name} - {self.client_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'wfm.visit',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('client_id', '=', self.client_id.id)
            ],
            'context': {'default_partner_id': self.partner_id.id, 'default_client_id': self.client_id.id}
        }
