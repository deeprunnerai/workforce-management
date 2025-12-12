from odoo import models, fields, api, _


class WfmContractService(models.Model):
    _name = 'wfm.contract.service'
    _description = 'Contract Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True
    )
    code = fields.Char(
        string='Service Code',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    # Contract relation
    contract_id = fields.Many2one(
        'wfm.contract',
        string='Contract',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    client_id = fields.Many2one(
        related='contract_id.client_id',
        string='Client',
        store=True
    )

    # Service type
    service_type = fields.Selection([
        ('physician', 'Occupational Physician (Ιατρός Εργασίας)'),
        ('safety_engineer', 'Safety Engineer (Τεχνικός Ασφαλείας)'),
        ('risk_assessment', 'Risk Assessment (ΓΕΕΚ)'),
        ('measurements', 'Factor Measurements (Μετρήσεις Παραγόντων)'),
        ('training', 'Training (Εκπαίδευση)'),
        ('consulting', 'Consulting (Συμβουλευτικές)'),
        ('other', 'Other'),
    ], string='Service Type', required=True, tracking=True)

    # Dates
    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True
    )
    end_date = fields.Date(
        string='End Date',
        tracking=True
    )

    # Hours and pricing
    assigned_hours = fields.Float(
        string='Assigned Hours',
        digits=(10, 2),
        help='Total hours allocated for this service period'
    )
    price_per_hour = fields.Monetary(
        string='Price per Hour',
        currency_field='currency_id',
        help='Hourly rate for this service'
    )
    quantity = fields.Float(
        string='Quantity',
        digits=(10, 2),
        default=1,
        help='For fixed-price services (e.g., 1 risk assessment)'
    )
    price_per_unit = fields.Monetary(
        string='Price per Unit',
        currency_field='currency_id',
        help='Fixed price per unit for non-hourly services'
    )
    currency_id = fields.Many2one(
        related='contract_id.currency_id',
        string='Currency'
    )

    # Computed revenue
    revenue = fields.Monetary(
        string='Revenue',
        compute='_compute_revenue',
        store=True,
        currency_field='currency_id'
    )

    # Status
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # Related installation services
    installation_service_ids = fields.One2many(
        'wfm.installation.service',
        'contract_service_id',
        string='Installation Services'
    )
    installation_service_count = fields.Integer(
        string='Installation Services',
        compute='_compute_installation_service_count'
    )

    @api.depends('contract_id.code', 'service_type')
    def _compute_name(self):
        service_labels = dict(self._fields['service_type'].selection)
        for record in self:
            if record.contract_id and record.service_type:
                service_name = service_labels.get(record.service_type, record.service_type)
                record.name = f"{record.contract_id.code} - {service_name}"
            else:
                record.name = record.code or _('New')

    @api.depends('assigned_hours', 'price_per_hour', 'quantity', 'price_per_unit')
    def _compute_revenue(self):
        for record in self:
            hourly_revenue = (record.assigned_hours or 0) * (record.price_per_hour or 0)
            unit_revenue = (record.quantity or 0) * (record.price_per_unit or 0)
            record.revenue = hourly_revenue + unit_revenue

    @api.depends('installation_service_ids')
    def _compute_installation_service_count(self):
        for record in self:
            record.installation_service_count = len(record.installation_service_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('wfm.contract.service') or _('New')
        return super().create(vals_list)

    def action_activate(self):
        self.write({'state': 'active'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
