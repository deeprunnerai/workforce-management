from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PartnerAvailability(models.Model):
    _name = 'wfm.partner.availability'
    _description = 'Partner Unavailability Period'
    _order = 'date_from desc'

    def _default_partner_id(self):
        return self.env.user.partner_id.id

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        domain=[('is_wfm_partner', '=', True)],
        default=_default_partner_id,
    )
    date_from = fields.Date(
        string='From Date',
        required=True,
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
    )
    reason = fields.Selection([
        ('vacation', 'Vacation'),
        ('sick', 'Sick Leave'),
        ('personal', 'Personal'),
        ('training', 'Training'),
        ('other', 'Other'),
    ], string='Reason', default='personal')
    notes = fields.Text(string='Notes')

    # Computed field for display
    name = fields.Char(
        string='Description',
        compute='_compute_name',
        store=True,
    )

    @api.depends('partner_id', 'date_from', 'date_to', 'reason')
    def _compute_name(self):
        for record in self:
            if record.partner_id and record.date_from and record.date_to:
                reason_label = dict(self._fields['reason'].selection).get(record.reason, '')
                record.name = f"{record.partner_id.name}: {record.date_from} - {record.date_to} ({reason_label})"
            else:
                record.name = _('New Unavailability')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_from > record.date_to:
                    raise ValidationError(_('End date must be after start date.'))

    @api.constrains('partner_id', 'date_from', 'date_to')
    def _check_overlap(self):
        for record in self:
            if record.partner_id and record.date_from and record.date_to:
                overlapping = self.search([
                    ('id', '!=', record.id),
                    ('partner_id', '=', record.partner_id.id),
                    ('date_from', '<=', record.date_to),
                    ('date_to', '>=', record.date_from),
                ])
                if overlapping:
                    raise ValidationError(_(
                        'This unavailability period overlaps with an existing one: %s'
                    ) % overlapping[0].name)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    availability_ids = fields.One2many(
        'wfm.partner.availability',
        'partner_id',
        string='Unavailability Periods',
    )

    def is_available_on_date(self, date):
        """Check if partner is available on a specific date"""
        self.ensure_one()
        unavailable = self.env['wfm.partner.availability'].search_count([
            ('partner_id', '=', self.id),
            ('date_from', '<=', date),
            ('date_to', '>=', date),
        ])
        return unavailable == 0

    @api.model
    def action_open_my_profile(self):
        """Open the current user's partner record for editing"""
        partner_id = self.env.user.partner_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('My Profile'),
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': partner_id,
            'view_id': self.env.ref('wfm_portal.wfm_partner_profile_form').id,
            'target': 'current',
        }
