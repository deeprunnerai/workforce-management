from odoo import models, fields, api


class WfmInstallation(models.Model):
    _name = 'wfm.installation'
    _description = 'Client Installation/Branch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Installation Name',
        required=True,
        tracking=True,
        help='Name of the installation/branch'
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
        required=True,
        domain=[('is_wfm_client', '=', True)],
        tracking=True,
        help='Client company this installation belongs to'
    )

    # Address fields
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    postal_code = fields.Char(string='Postal Code')
    country_id = fields.Many2one('res.country', string='Country')

    # Computed full address
    address = fields.Char(
        string='Full Address',
        compute='_compute_address',
        store=True
    )

    employee_count = fields.Integer(
        string='Number of Employees',
        default=0,
        help='Number of employees at this installation'
    )
    installation_type = fields.Selection([
        ('office', 'Office'),
        ('warehouse', 'Warehouse'),
        ('factory', 'Factory'),
        ('retail', 'Retail'),
        ('construction', 'Construction Site'),
        ('other', 'Other'),
    ], string='Installation Type', default='office', tracking=True)

    visit_ids = fields.One2many(
        'wfm.visit',
        'installation_id',
        string='Visits'
    )
    visit_count = fields.Integer(
        string='Visit Count',
        compute='_compute_visit_count'
    )

    active = fields.Boolean(default=True)

    @api.depends('street', 'street2', 'city', 'postal_code', 'country_id')
    def _compute_address(self):
        for record in self:
            parts = [record.street, record.street2, record.city, record.postal_code]
            if record.country_id:
                parts.append(record.country_id.name)
            record.address = ', '.join(filter(None, parts))

    @api.depends('visit_ids')
    def _compute_visit_count(self):
        for record in self:
            record.visit_count = len(record.visit_ids)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} ({record.client_id.name})" if record.client_id else record.name
            result.append((record.id, name))
        return result
