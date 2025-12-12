from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WfmVisit(models.Model):
    _name = 'wfm.visit'
    _description = 'OHS Visit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_date desc, id desc'

    name = fields.Char(
        string='Visit Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    # Relations
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
        required=True,
        domain=[('is_wfm_client', '=', True)],
        tracking=True
    )
    installation_id = fields.Many2one(
        'wfm.installation',
        string='Installation',
        required=True,
        tracking=True
    )
    installation_service_id = fields.Many2one(
        'wfm.installation.service',
        string='Installation Service',
        tracking=True,
        help='Link to the specific service assignment for this installation'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Assigned Partner',
        domain=[('is_wfm_partner', '=', True)],
        tracking=True,
        help='OHS professional assigned to this visit'
    )

    # Scheduling
    visit_date = fields.Date(
        string='Visit Date',
        required=True,
        tracking=True,
        default=fields.Date.context_today
    )
    start_time = fields.Float(
        string='Start Time',
        default=9.0,
        help='Start time in 24h format (e.g., 9.5 = 9:30 AM)'
    )
    end_time = fields.Float(
        string='End Time',
        default=17.0,
        help='End time in 24h format (e.g., 17.5 = 5:30 PM)'
    )
    duration = fields.Float(
        string='Duration (hours)',
        compute='_compute_duration',
        store=True
    )

    # Stage and State
    stage_id = fields.Many2one(
        'wfm.visit.stage',
        string='Stage',
        tracking=True,
        group_expand='_read_group_stage_ids',
        default=lambda self: self._get_default_stage(),
        copy=False
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)

    # For Kanban color coding
    color = fields.Integer(
        string='Color',
        compute='_compute_color'
    )
    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Ready'),
        ('blocked', 'Blocked'),
    ], string='Kanban State', default='normal', copy=False)

    # Additional info
    notes = fields.Text(string='Notes')
    visit_type = fields.Selection([
        ('regular', 'Regular Visit'),
        ('urgent', 'Urgent'),
        ('follow_up', 'Follow-up'),
    ], string='Visit Type', default='regular')

    # Partner info (denormalized for easy display)
    partner_phone = fields.Char(
        related='partner_id.phone',
        string='Partner Phone',
        readonly=True
    )
    partner_specialty = fields.Selection(
        related='partner_id.specialty',
        string='Partner Specialty',
        readonly=True
    )

    # Installation info (denormalized)
    installation_address = fields.Char(
        related='installation_id.address',
        string='Address',
        readonly=True
    )

    active = fields.Boolean(default=True)

    @api.model
    def _get_default_stage(self):
        """Get the first stage by sequence."""
        return self.env['wfm.visit.stage'].search([], limit=1, order='sequence')

    def _read_group_stage_ids(self, stages, domain):
        """Always display all stages in Kanban view (Odoo 19 compatible)."""
        return self.env['wfm.visit.stage'].search([], order='sequence')

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for visit in self:
            if visit.end_time and visit.start_time:
                visit.duration = visit.end_time - visit.start_time
            else:
                visit.duration = 0.0

    @api.depends('state', 'visit_date')
    def _compute_color(self):
        """
        Color coding for dashboard:
        - Green (10): Completed
        - Yellow (3): Assigned, future date
        - Orange (2): In Progress
        - Red (1): Action required (draft with past date, blocked)
        """
        today = fields.Date.context_today(self)
        for visit in self:
            if visit.state == 'done':
                visit.color = 10  # Green
            elif visit.state == 'in_progress':
                visit.color = 2  # Orange
            elif visit.state in ('assigned', 'confirmed'):
                visit.color = 3  # Yellow
            elif visit.state == 'draft' and visit.visit_date and visit.visit_date < today:
                visit.color = 1  # Red - overdue
            elif visit.state == 'cancelled':
                visit.color = 0  # Gray
            else:
                visit.color = 0  # Default

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wfm.visit') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        """Override write to trigger notifications on partner assignment."""
        result = super().write(vals)

        # Trigger notification agent when partner is assigned
        if 'partner_id' in vals and vals['partner_id']:
            self._trigger_notification_agent()

        return result

    def _trigger_notification_agent(self):
        """
        Autonomous Notification Agent - called when partner is assigned.
        This method is a hook for wfm_whatsapp module to extend.
        """
        for visit in self:
            # Send in-app notification
            if visit.partner_id:
                visit.message_notify(
                    partner_ids=visit.partner_id.ids,
                    body=_(
                        'You have been assigned to visit %(client)s at %(location)s on %(date)s',
                        client=visit.client_id.name,
                        location=visit.installation_id.name,
                        date=visit.visit_date,
                    ),
                    subject=_('New Visit Assignment'),
                )

    def action_assign(self):
        """Assign the visit (change state to assigned)."""
        self.write({'state': 'assigned'})

    def action_confirm(self):
        """Confirm the visit."""
        self.write({'state': 'confirmed'})

    def action_start(self):
        """Start the visit."""
        self.write({'state': 'in_progress'})

    def action_complete(self):
        """Complete the visit."""
        self.write({'state': 'done'})

    def action_cancel(self):
        """Cancel the visit."""
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """Reset to draft state."""
        self.write({'state': 'draft'})

    @api.onchange('client_id')
    def _onchange_client_id(self):
        """Filter installations by selected client."""
        self.installation_id = False
        if self.client_id:
            return {
                'domain': {
                    'installation_id': [('client_id', '=', self.client_id.id)]
                }
            }
        return {'domain': {'installation_id': []}}

    @api.constrains('start_time', 'end_time')
    def _check_times(self):
        for visit in self:
            if visit.start_time and visit.end_time:
                if visit.start_time >= visit.end_time:
                    raise ValidationError(_('End time must be after start time.'))
                if visit.start_time < 0 or visit.start_time >= 24:
                    raise ValidationError(_('Start time must be between 0 and 24.'))
                if visit.end_time < 0 or visit.end_time > 24:
                    raise ValidationError(_('End time must be between 0 and 24.'))
