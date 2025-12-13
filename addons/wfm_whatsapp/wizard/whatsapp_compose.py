from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WfmWhatsAppCompose(models.TransientModel):
    """Wizard to compose and send WhatsApp messages."""

    _name = 'wfm.whatsapp.compose'
    _description = 'Compose WhatsApp Message'

    visit_id = fields.Many2one(
        'wfm.visit',
        string='Visit',
        required=True,
        readonly=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Recipient',
        required=True,
        readonly=True
    )
    partner_phone = fields.Char(
        related='partner_id.phone',
        string='Phone',
        readonly=True
    )

    # Template selection
    template = fields.Selection([
        ('assignment', 'Assignment Notification'),
        ('confirmed', 'Confirmation'),
        ('reminder', '24h Reminder'),
        ('cancelled', 'Cancellation Notice'),
        ('custom', 'Custom Message'),
    ], string='Template', default='custom', required=True)

    # Message content
    message_body = fields.Text(
        string='Message',
        required=True
    )

    # Preview
    preview = fields.Html(
        string='Preview',
        compute='_compute_preview',
        sanitize=False
    )

    @api.onchange('template')
    def _onchange_template(self):
        """Load template content when template changes."""
        if not self.visit_id:
            return

        if self.template == 'assignment':
            self.message_body = self.visit_id._get_assignment_message()
        elif self.template == 'confirmed':
            self.message_body = self.visit_id._get_confirmed_message()
        elif self.template == 'reminder':
            self.message_body = self.visit_id._get_reminder_message()
        elif self.template == 'cancelled':
            self.message_body = self.visit_id._get_cancelled_message()
        elif self.template == 'custom':
            self.message_body = f"""📨 Message from GEP Coordinator

[Your message here]

---
Re: {self.visit_id.name}
{self.visit_id.visit_date} at {self.visit_id.client_id.name or 'N/A'}"""

    @api.depends('message_body')
    def _compute_preview(self):
        """Generate HTML preview of the message."""
        for rec in self:
            if rec.message_body:
                # Convert newlines to <br> for HTML display
                html_body = rec.message_body.replace('\n', '<br/>')
                rec.preview = f"""
                <div style="background: #dcf8c6; border-radius: 10px; padding: 15px; max-width: 400px; font-family: sans-serif;">
                    <div style="font-size: 12px; color: #666; margin-bottom: 5px;">
                        To: {rec.partner_id.name} ({rec.partner_phone or 'No phone'})
                    </div>
                    <div style="font-size: 14px;">
                        {html_body}
                    </div>
                </div>
                """
            else:
                rec.preview = '<p class="text-muted">Enter a message to see preview</p>'

    def action_send(self):
        """Send the WhatsApp message."""
        self.ensure_one()

        if not self.message_body:
            raise UserError(_("Please enter a message."))

        if not self.partner_phone and not self.partner_id.phone:
            raise UserError(_("Partner has no phone number configured."))

        # Send via WhatsApp message model
        message = self.env['wfm.whatsapp.message'].send_message(
            partner_id=self.partner_id,
            message_body=self.message_body,
            message_type=self.template,
            visit_id=self.visit_id
        )

        if message and message.status == 'sent':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('WhatsApp Sent'),
                    'message': _('Message sent to %s') % self.partner_id.name,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            error = message.error_message if message else 'Unknown error'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Send Failed'),
                    'message': _('Failed to send: %s') % error,
                    'type': 'danger',
                    'sticky': True,
                }
            }
