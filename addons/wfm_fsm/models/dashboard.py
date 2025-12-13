from odoo import models, fields, api, _


class WfmDashboard(models.Model):
    """Dashboard model for coordinator statistics."""
    _name = 'wfm.dashboard'
    _description = 'WFM Coordinator Dashboard'

    name = fields.Char(string='Dashboard', default='Coordinator Dashboard')

    # Computed stats - not stored, always fresh
    green_count = fields.Integer(
        string='Completed',
        compute='_compute_dashboard_stats'
    )
    yellow_count = fields.Integer(
        string='Assigned',
        compute='_compute_dashboard_stats'
    )
    orange_count = fields.Integer(
        string='In Progress',
        compute='_compute_dashboard_stats'
    )
    red_count = fields.Integer(
        string='Action Required',
        compute='_compute_dashboard_stats'
    )
    total_visits = fields.Integer(
        string='Total Visits',
        compute='_compute_dashboard_stats'
    )
    today_visits = fields.Integer(
        string="Today's Visits",
        compute='_compute_dashboard_stats'
    )
    unassigned_visits = fields.Integer(
        string='Unassigned',
        compute='_compute_dashboard_stats'
    )
    week_visits = fields.Integer(
        string='This Week',
        compute='_compute_dashboard_stats'
    )

    def _compute_dashboard_stats(self):
        """Compute all dashboard statistics."""
        Visit = self.env['wfm.visit']
        stats = Visit.get_dashboard_data()
        for rec in self:
            rec.green_count = stats.get('green', 0)
            rec.yellow_count = stats.get('yellow', 0)
            rec.orange_count = stats.get('orange', 0)
            rec.red_count = stats.get('red', 0)
            rec.total_visits = stats.get('total', 0)
            rec.today_visits = stats.get('today', 0)
            rec.unassigned_visits = stats.get('unassigned', 0)
            rec.week_visits = stats.get('this_week', 0)

    def action_view_green(self):
        """View completed visits."""
        return self.env['wfm.visit'].get_visits_by_state('green')

    def action_view_yellow(self):
        """View assigned visits."""
        return self.env['wfm.visit'].get_visits_by_state('yellow')

    def action_view_orange(self):
        """View in-progress visits."""
        return self.env['wfm.visit'].get_visits_by_state('orange')

    def action_view_red(self):
        """View action-required visits."""
        return self.env['wfm.visit'].get_visits_by_state('red')

    def action_view_today(self):
        """View today's visits."""
        return self.env['wfm.visit'].get_visits_by_state('today')

    def action_view_unassigned(self):
        """View unassigned visits."""
        return self.env['wfm.visit'].get_visits_by_state('unassigned')

    @api.model
    def get_or_create_dashboard(self):
        """Get existing dashboard or create one."""
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({'name': 'Coordinator Dashboard'})
        return dashboard.id
