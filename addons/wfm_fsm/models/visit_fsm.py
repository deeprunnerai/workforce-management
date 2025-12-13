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
        """Complete the visit."""
        stage_id = self._get_stage_for_state('done')
        self.write({'state': 'done', 'stage_id': stage_id})

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
