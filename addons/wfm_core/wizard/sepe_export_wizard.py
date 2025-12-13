from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SepeExportWizard(models.TransientModel):
    _name = 'wfm.sepe.export.wizard'
    _description = 'SEPE Export Wizard'

    date_from = fields.Date(
        required=True,
        string='From Date',
        default=lambda self: fields.Date.today().replace(day=1)
    )
    date_to = fields.Date(
        required=True,
        string='To Date',
        default=fields.Date.today
    )
    include_exported = fields.Boolean(
        default=False,
        string='Include Already Exported',
        help='Include visits that were previously exported to SEPE'
    )

    visit_ids = fields.Many2many(
        'wfm.visit',
        compute='_compute_visits',
        string='Visits to Export'
    )
    visit_count = fields.Integer(
        compute='_compute_visits',
        string='Visit Count'
    )
    total_hours = fields.Float(
        compute='_compute_visits',
        string='Total Hours'
    )
    total_amount = fields.Monetary(
        compute='_compute_visits',
        string='Total Amount',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    @api.depends('date_from', 'date_to', 'include_exported')
    def _compute_visits(self):
        for wizard in self:
            domain = [
                ('visit_date', '>=', wizard.date_from),
                ('visit_date', '<=', wizard.date_to),
                ('state', '=', 'done'),
            ]
            if not wizard.include_exported:
                domain.append(('sepe_exported', '=', False))

            visits = self.env['wfm.visit'].search(domain)
            wizard.visit_ids = visits
            wizard.visit_count = len(visits)
            wizard.total_hours = sum(visits.mapped('duration'))
            wizard.total_amount = sum(visits.mapped('partner_payment_amount'))

    def action_create_export(self):
        """Create SEPE export batch and generate Excel."""
        self.ensure_one()

        if not self.visit_ids:
            raise UserError(_('No completed visits found for the selected date range.'))

        export = self.env['wfm.sepe.export'].create({
            'date_from': self.date_from,
            'date_to': self.date_to,
            'visit_ids': [(6, 0, self.visit_ids.ids)],
        })

        export.action_generate_excel()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wfm.sepe.export',
            'res_id': export.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_preview_visits(self):
        """Preview visits that will be exported."""
        self.ensure_one()

        if not self.visit_ids:
            raise UserError(_('No completed visits found for the selected date range.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Visits to Export'),
            'res_model': 'wfm.visit',
            'domain': [('id', 'in', self.visit_ids.ids)],
            'view_mode': 'list,form',
            'target': 'current',
        }
