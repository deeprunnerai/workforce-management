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

    # Filters
    client_ids = fields.Many2many(
        'res.partner',
        'sepe_wizard_client_rel',
        'wizard_id', 'partner_id',
        string='Clients',
        domain="[('is_wfm_client', '=', True)]",
        help='Filter by specific clients. Leave empty to include all.'
    )
    partner_ids = fields.Many2many(
        'res.partner',
        'sepe_wizard_partner_rel',
        'wizard_id', 'partner_id',
        string='Partners',
        domain="[('is_wfm_partner', '=', True)]",
        help='Filter by specific partners. Leave empty to include all.'
    )

    include_exported = fields.Boolean(
        default=False,
        string='Include Already Exported',
        help='Include visits that were previously exported to SEPE'
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    def _get_visit_domain(self):
        """Build domain for visit search based on wizard filters."""
        self.ensure_one()
        domain = [
            ('visit_date', '>=', self.date_from),
            ('visit_date', '<=', self.date_to),
            ('state', '=', 'done'),
        ]
        if not self.include_exported:
            domain.append(('sepe_exported', '=', False))

        if self.client_ids:
            domain.append(('client_id', 'in', self.client_ids.ids))

        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))

        return domain

    def action_create_export(self):
        """Create SEPE export batch and generate Excel."""
        self.ensure_one()

        domain = self._get_visit_domain()
        visits = self.env['wfm.visit'].search(domain)

        if not visits:
            raise UserError(_('No completed visits found for the selected criteria.'))

        export = self.env['wfm.sepe.export'].create({
            'date_from': self.date_from,
            'date_to': self.date_to,
            'visit_ids': [(6, 0, visits.ids)],
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

        domain = self._get_visit_domain()
        visits = self.env['wfm.visit'].search(domain)

        if not visits:
            raise UserError(_('No completed visits found for the selected criteria.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Visits to Export'),
            'res_model': 'wfm.visit',
            'domain': [('id', 'in', visits.ids)],
            'view_mode': 'list,form',
            'target': 'current',
        }
