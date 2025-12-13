from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WfmVisitAssignWizard(models.TransientModel):
    """Wizard for bulk assigning partners to visits."""
    _name = 'wfm.visit.assign.wizard'
    _description = 'Visit Assignment Wizard'

    visit_ids = fields.Many2many(
        'wfm.visit',
        string='Visits',
        required=True,
        default=lambda self: self._default_visit_ids()
    )
    visit_count = fields.Integer(
        string='Visit Count',
        compute='_compute_visit_count'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Assign Partner',
        domain=[('is_wfm_partner', '=', True)],
        required=True
    )

    # Filters for partner selection
    specialty_filter = fields.Selection([
        ('physician', 'Occupational Physician'),
        ('safety_engineer', 'Safety Engineer'),
        ('health_scientist', 'Health Scientist'),
    ], string='Filter by Specialty')

    city_filter = fields.Char(string='Filter by City')

    # Info fields
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
        readonly=True
    )
    installation_id = fields.Many2one(
        'wfm.installation',
        string='Installation',
        readonly=True
    )

    # Partner suggestions
    suggested_partner_ids = fields.Many2many(
        'res.partner',
        string='Suggested Partners',
        compute='_compute_suggested_partners'
    )

    def _default_visit_ids(self):
        """Get visits from context."""
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            return [(6, 0, active_ids)]
        return []

    @api.depends('visit_ids')
    def _compute_visit_count(self):
        for wizard in self:
            wizard.visit_count = len(wizard.visit_ids)

    @api.depends('specialty_filter', 'city_filter', 'installation_id')
    def _compute_suggested_partners(self):
        """Compute suggested partners based on filters and proximity."""
        Partner = self.env['res.partner']
        for wizard in self:
            domain = [('is_wfm_partner', '=', True)]

            if wizard.specialty_filter:
                domain.append(('specialty', '=', wizard.specialty_filter))

            if wizard.city_filter:
                domain.append(('city', 'ilike', wizard.city_filter))

            # If installation has a city, suggest partners from same city
            if wizard.installation_id and wizard.installation_id.city:
                domain.append(('city', 'ilike', wizard.installation_id.city))

            partners = Partner.search(domain, limit=10, order='name')
            wizard.suggested_partner_ids = partners

    @api.onchange('specialty_filter', 'city_filter')
    def _onchange_filters(self):
        """Update partner domain based on filters."""
        domain = [('is_wfm_partner', '=', True)]
        if self.specialty_filter:
            domain.append(('specialty', '=', self.specialty_filter))
        if self.city_filter:
            domain.append(('city', 'ilike', self.city_filter))
        return {'domain': {'partner_id': domain}}

    def action_assign(self):
        """Assign the selected partner to all visits."""
        self.ensure_one()

        if not self.visit_ids:
            raise UserError(_('No visits selected for assignment.'))

        if not self.partner_id:
            raise UserError(_('Please select a partner to assign.'))

        # Check for draft visits only
        non_draft = self.visit_ids.filtered(lambda v: v.state != 'draft')
        if non_draft:
            raise UserError(_(
                'Some visits are not in Draft state and cannot be reassigned. '
                'Please select only Draft visits or reset them first.'
            ))

        # Assign partner and update state
        self.visit_ids.write({
            'partner_id': self.partner_id.id,
            'state': 'assigned',
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%d visit(s) assigned to %s') % (
                    len(self.visit_ids), self.partner_id.name
                ),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_assign_and_view(self):
        """Assign and view the assigned visits."""
        self.action_assign()
        return {
            'name': _('Assigned Visits'),
            'type': 'ir.actions.act_window',
            'res_model': 'wfm.visit',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', self.visit_ids.ids)],
        }
