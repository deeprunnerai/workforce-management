from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # WFM Client fields
    is_wfm_client = fields.Boolean(
        string='Is WFM Client',
        default=False,
        help='Check if this partner is a WFM client (company purchasing OHS services)'
    )
    installation_ids = fields.One2many(
        'wfm.installation',
        'client_id',
        string='Installations',
        help='Installations/branches belonging to this client'
    )
    installation_count = fields.Integer(
        string='Installation Count',
        compute='_compute_installation_count'
    )

    # WFM Partner (Resource) fields
    is_wfm_partner = fields.Boolean(
        string='Is WFM Partner',
        default=False,
        help='Check if this partner is an OHS professional (physician, safety engineer)'
    )
    specialty = fields.Selection([
        ('physician', 'Occupational Physician'),
        ('safety_engineer', 'Safety Engineer'),
        ('health_scientist', 'Health Scientist'),
    ], string='Specialty', help='OHS professional specialty')
    hourly_rate = fields.Float(
        string='Hourly Rate',
        digits=(10, 2),
        help='Hourly rate in EUR for this partner'
    )
    wfm_visit_ids = fields.One2many(
        'wfm.visit',
        'partner_id',
        string='Assigned Visits',
        help='Visits assigned to this partner'
    )
    visit_count = fields.Integer(
        string='Visit Count',
        compute='_compute_visit_count'
    )

    @api.depends('installation_ids')
    def _compute_installation_count(self):
        for partner in self:
            partner.installation_count = len(partner.installation_ids)

    @api.depends('wfm_visit_ids')
    def _compute_visit_count(self):
        for partner in self:
            partner.visit_count = len(partner.wfm_visit_ids)
