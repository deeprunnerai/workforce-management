from odoo import models, fields, api, _


class WfmInstallationService(models.Model):
    _name = 'wfm.installation.service'
    _description = 'Installation Service Assignment'
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

    # Contract Service relation (parent)
    contract_service_id = fields.Many2one(
        'wfm.contract.service',
        string='Contract Service',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    contract_id = fields.Many2one(
        related='contract_service_id.contract_id',
        string='Contract',
        store=True
    )
    client_id = fields.Many2one(
        related='contract_service_id.client_id',
        string='Client',
        store=True
    )
    service_type = fields.Selection(
        related='contract_service_id.service_type',
        string='Service Type',
        store=True
    )

    # Installation relation
    installation_id = fields.Many2one(
        'wfm.installation',
        string='Installation',
        required=True,
        tracking=True
    )
    installation_address = fields.Char(
        related='installation_id.address',
        string='Address'
    )

    # Partner (Resource) assignment
    partner_id = fields.Many2one(
        'res.partner',
        string='Assigned Partner',
        domain=[('is_wfm_partner', '=', True)],
        tracking=True,
        help='OHS professional assigned to this installation service'
    )
    partner_specialty = fields.Selection(
        related='partner_id.specialty',
        string='Partner Specialty'
    )

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

    # Hours tracking
    assigned_hours = fields.Float(
        string='Assigned Hours',
        digits=(10, 2),
        help='Hours allocated for this installation in this service period'
    )
    programmed_hours = fields.Float(
        string='Programmed Hours',
        compute='_compute_programmed_hours',
        store=True,
        help='Sum of visit durations (scheduled)'
    )
    completed_hours = fields.Float(
        string='Completed Hours',
        compute='_compute_completed_hours',
        store=True,
        help='Sum of completed visit durations'
    )
    remaining_hours = fields.Float(
        string='Remaining Hours',
        compute='_compute_remaining_hours',
        store=True
    )

    # Status
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # Related visits
    visit_ids = fields.One2many(
        'wfm.visit',
        'installation_service_id',
        string='Visits'
    )
    visit_count = fields.Integer(
        string='Visits',
        compute='_compute_visit_count'
    )

    @api.depends('installation_id', 'contract_service_id.service_type', 'partner_id')
    def _compute_name(self):
        service_labels = dict(self.env['wfm.contract.service']._fields['service_type'].selection)
        for record in self:
            parts = []
            if record.installation_id:
                parts.append(record.installation_id.name)
            if record.service_type:
                parts.append(service_labels.get(record.service_type, record.service_type))
            if record.partner_id:
                parts.append(record.partner_id.name)
            record.name = ' - '.join(parts) if parts else record.code or _('New')

    @api.depends('visit_ids', 'visit_ids.duration')
    def _compute_programmed_hours(self):
        for record in self:
            record.programmed_hours = sum(record.visit_ids.mapped('duration'))

    @api.depends('visit_ids', 'visit_ids.duration', 'visit_ids.state')
    def _compute_completed_hours(self):
        for record in self:
            completed_visits = record.visit_ids.filtered(lambda v: v.state == 'done')
            record.completed_hours = sum(completed_visits.mapped('duration'))

    @api.depends('assigned_hours', 'programmed_hours')
    def _compute_remaining_hours(self):
        for record in self:
            record.remaining_hours = (record.assigned_hours or 0) - (record.programmed_hours or 0)

    @api.depends('visit_ids')
    def _compute_visit_count(self):
        for record in self:
            record.visit_count = len(record.visit_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('wfm.installation.service') or _('New')
        return super().create(vals_list)

    @api.onchange('contract_service_id')
    def _onchange_contract_service_id(self):
        """Set dates from contract service and filter installations by client."""
        if self.contract_service_id:
            self.start_date = self.contract_service_id.start_date
            self.end_date = self.contract_service_id.end_date
            return {
                'domain': {
                    'installation_id': [('client_id', '=', self.contract_service_id.client_id.id)]
                }
            }
        return {'domain': {'installation_id': []}}

    def action_assign(self):
        self.write({'state': 'assigned'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_create_visit(self):
        """Quick action to create a visit for this installation service."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Visit'),
            'res_model': 'wfm.visit',
            'view_mode': 'form',
            'context': {
                'default_installation_service_id': self.id,
                'default_client_id': self.client_id.id,
                'default_installation_id': self.installation_id.id,
                'default_partner_id': self.partner_id.id,
            },
            'target': 'current',
        }
