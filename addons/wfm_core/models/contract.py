from odoo import models, fields, api, _
from datetime import date


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

    # Statistics fields (computed for active state view)
    total_visits = fields.Integer(
        string='Total Visits',
        compute='_compute_statistics',
        store=False
    )
    completed_visits = fields.Integer(
        string='Completed Visits',
        compute='_compute_statistics',
        store=False
    )
    pending_visits = fields.Integer(
        string='Pending Visits',
        compute='_compute_statistics',
        store=False
    )
    total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_statistics',
        store=False
    )
    total_revenue = fields.Monetary(
        string='Total Revenue',
        compute='_compute_statistics',
        currency_field='currency_id',
        store=False
    )
    completion_rate = fields.Float(
        string='Completion Rate (%)',
        compute='_compute_statistics',
        store=False
    )
    assigned_hours = fields.Float(
        string='Assigned Hours',
        compute='_compute_statistics',
        store=False
    )
    utilization_rate = fields.Float(
        string='Utilization Rate (%)',
        compute='_compute_statistics',
        store=False
    )
    days_remaining = fields.Integer(
        string='Days Remaining',
        compute='_compute_days_remaining',
        store=False
    )
    days_active = fields.Integer(
        string='Days Active',
        compute='_compute_days_remaining',
        store=False
    )

    # Timeline fields (for expired state view)
    activation_date = fields.Date(
        string='Activation Date',
        help='Date when contract was activated'
    )
    expiration_date = fields.Date(
        string='Actual Expiration Date',
        help='Actual date when contract expired'
    )

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
        self.write({
            'state': 'active',
            'activation_date': date.today()
        })

    def action_expire(self):
        self.write({
            'state': 'expired',
            'expiration_date': date.today()
        })

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    @api.depends('client_id', 'start_date', 'end_date')
    def _compute_statistics(self):
        """Compute visit statistics for the contract period."""
        Visit = self.env['wfm.visit']
        for contract in self:
            if not contract.client_id:
                contract.total_visits = 0
                contract.completed_visits = 0
                contract.pending_visits = 0
                contract.total_hours = 0.0
                contract.total_revenue = 0.0
                contract.completion_rate = 0.0
                contract.assigned_hours = 0.0
                contract.utilization_rate = 0.0
                continue

            # Build domain for visits within contract period
            domain = [('client_id', '=', contract.client_id.id)]
            if contract.start_date:
                domain.append(('visit_date', '>=', contract.start_date))
            if contract.end_date:
                domain.append(('visit_date', '<=', contract.end_date))

            visits = Visit.search(domain)
            completed = visits.filtered(lambda v: v.state == 'done')

            contract.total_visits = len(visits)
            contract.completed_visits = len(completed)
            contract.pending_visits = len(visits) - len(completed)
            contract.total_hours = sum(completed.mapped('duration'))
            contract.total_revenue = sum(completed.mapped('partner_payment_amount'))

            if contract.total_visits > 0:
                contract.completion_rate = (contract.completed_visits / contract.total_visits) * 100
            else:
                contract.completion_rate = 0.0

            # Calculate assigned hours from services
            contract.assigned_hours = sum(contract.service_ids.mapped('assigned_hours'))

            if contract.assigned_hours > 0:
                contract.utilization_rate = (contract.total_hours / contract.assigned_hours) * 100
            else:
                contract.utilization_rate = 0.0

    @api.depends('start_date', 'end_date', 'state')
    def _compute_days_remaining(self):
        """Compute days remaining and days active."""
        today = date.today()
        for contract in self:
            if contract.start_date:
                contract.days_active = (today - contract.start_date).days
            else:
                contract.days_active = 0

            if contract.end_date and contract.state == 'active':
                remaining = (contract.end_date - today).days
                contract.days_remaining = max(0, remaining)
            else:
                contract.days_remaining = 0
