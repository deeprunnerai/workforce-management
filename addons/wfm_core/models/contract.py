from odoo import models, fields, api, _


class WfmContract(models.Model):
    _name = 'wfm.contract'
    _description = 'Client Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(
        string='Contract Name',
        required=True,
        tracking=True
    )
    code = fields.Char(
        string='Contract Code',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    # Client relation
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
        required=True,
        domain=[('is_wfm_client', '=', True)],
        tracking=True
    )
    client_name = fields.Char(
        related='client_id.name',
        string='Client Name',
        store=True
    )

    # Contract details
    characterization = fields.Selection([
        ('main', 'Main (ΚΥΡΙΑ)'),
        ('secondary', 'Secondary'),
        ('amendment', 'Amendment'),
    ], string='Characterization', default='main', tracking=True)

    # Dates
    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True
    )
    end_date = fields.Date(
        string='End Date',
        tracking=True,
        help='Leave empty for indefinite contracts'
    )
    signed_date_aade = fields.Date(
        string='AADE Signed Date',
        tracking=True,
        help='Date contract was registered with AADE (tax authority)'
    )

    # Financial
    contract_value = fields.Monetary(
        string='Contract Value',
        currency_field='currency_id',
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # Flags
    is_indefinite = fields.Boolean(
        string='Indefinite Contract',
        default=False,
        tracking=True,
        help='Contract with no fixed end date (Αορίστου Χρόνου)'
    )
    active = fields.Boolean(default=True)

    # Related records
    service_ids = fields.One2many(
        'wfm.contract.service',
        'contract_id',
        string='Contract Services'
    )
    service_count = fields.Integer(
        string='Services',
        compute='_compute_service_count'
    )

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('service_ids')
    def _compute_service_count(self):
        for contract in self:
            contract.service_count = len(contract.service_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('wfm.contract') or _('New')
        return super().create(vals_list)

    @api.onchange('is_indefinite')
    def _onchange_is_indefinite(self):
        if self.is_indefinite:
            self.end_date = False

    def action_activate(self):
        self.write({'state': 'active'})

    def action_expire(self):
        self.write({'state': 'expired'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
