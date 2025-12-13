import logging
from datetime import timedelta

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class WfmVisitWhatsApp(models.Model):
    """Extend wfm.visit with WhatsApp notification capabilities."""

    _inherit = 'wfm.visit'

    # WhatsApp message history
    whatsapp_message_ids = fields.One2many(
        'wfm.whatsapp.message',
        'visit_id',
        string='WhatsApp Messages'
    )
    whatsapp_count = fields.Integer(
        compute='_compute_whatsapp_count',
        string='Messages'
    )

    @api.depends('whatsapp_message_ids')
    def _compute_whatsapp_count(self):
        for visit in self:
            visit.whatsapp_count = len(visit.whatsapp_message_ids)

    def write(self, vals):
        """Override write to trigger WhatsApp notifications on key events."""
        # Track changes before write
        partner_assigned = {}
        state_changed = {}

        for visit in self:
            if 'partner_id' in vals:
                old_partner = visit.partner_id.id
                new_partner = vals.get('partner_id')
                if new_partner and new_partner != old_partner:
                    partner_assigned[visit.id] = new_partner

            if 'state' in vals:
                old_state = visit.state
                new_state = vals.get('state')
                if new_state != old_state:
                    state_changed[visit.id] = (old_state, new_state)

        result = super().write(vals)

        # Send notifications after successful write
        for visit_id, new_partner_id in partner_assigned.items():
            visit = self.browse(visit_id)
            visit._send_whatsapp_assignment()

        for visit_id, (old_state, new_state) in state_changed.items():
            visit = self.browse(visit_id)
            if new_state == 'cancelled':
                visit._send_whatsapp_cancelled()

        return result

    def _send_whatsapp_assignment(self):
        """Send WhatsApp notification when partner is assigned."""
        self.ensure_one()

        if not self.partner_id:
            return False

        message_body = self._get_assignment_message()

        return self.env['wfm.whatsapp.message'].send_message(
            partner_id=self.partner_id,
            message_body=message_body,
            message_type='assignment',
            visit_id=self
        )

    def _send_whatsapp_confirmed(self):
        """Send WhatsApp notification when visit is confirmed."""
        self.ensure_one()

        if not self.partner_id:
            return False

        message_body = self._get_confirmed_message()

        return self.env['wfm.whatsapp.message'].send_message(
            partner_id=self.partner_id,
            message_body=message_body,
            message_type='confirmed',
            visit_id=self
        )

    def _send_whatsapp_cancelled(self):
        """Send WhatsApp notification when visit is cancelled."""
        self.ensure_one()

        if not self.partner_id:
            return False

        message_body = self._get_cancelled_message()

        return self.env['wfm.whatsapp.message'].send_message(
            partner_id=self.partner_id,
            message_body=message_body,
            message_type='cancelled',
            visit_id=self
        )

    def _send_whatsapp_reminder(self):
        """Send 24-hour reminder WhatsApp."""
        self.ensure_one()

        if not self.partner_id:
            return False

        message_body = self._get_reminder_message()

        return self.env['wfm.whatsapp.message'].send_message(
            partner_id=self.partner_id,
            message_body=message_body,
            message_type='reminder',
            visit_id=self
        )

    def _get_assignment_message(self):
        """Build assignment notification message."""
        self.ensure_one()

        # Format time
        start_time = f"{int(self.start_time):02d}:{int((self.start_time % 1) * 60):02d}" if self.start_time else "TBD"
        end_time = f"{int(self.end_time):02d}:{int((self.end_time % 1) * 60):02d}" if self.end_time else "TBD"

        return f"""🏥 GEP OHS - New Visit Assignment

Hello {self.partner_id.name},

You have been assigned to a new visit:

📅 Date: {self.visit_date.strftime('%A, %d %B %Y') if self.visit_date else 'TBD'}
⏰ Time: {start_time} - {end_time}
🏢 Client: {self.client_id.name or 'N/A'}
📍 Location: {self.installation_id.name or 'N/A'}
   {self.installation_id.address or ''}, {self.installation_id.city or ''}

Please confirm your availability in the Partner Portal.

Reference: {self.name}"""

    def _get_confirmed_message(self):
        """Build confirmation acknowledgment message."""
        self.ensure_one()

        start_time = f"{int(self.start_time):02d}:{int((self.start_time % 1) * 60):02d}" if self.start_time else "TBD"
        end_time = f"{int(self.end_time):02d}:{int((self.end_time % 1) * 60):02d}" if self.end_time else "TBD"

        return f"""✅ Visit Confirmed

Your visit on {self.visit_date.strftime('%d/%m/%Y') if self.visit_date else 'TBD'} at {self.client_id.name or 'N/A'} has been confirmed.

📍 {self.installation_id.address or ''}, {self.installation_id.city or ''}
⏰ {start_time} - {end_time}

Reference: {self.name}

See you there!"""

    def _get_cancelled_message(self):
        """Build cancellation notice message."""
        self.ensure_one()

        return f"""❌ Visit Cancelled

The following visit has been cancelled:

📅 {self.visit_date.strftime('%d/%m/%Y') if self.visit_date else 'TBD'}
🏢 {self.client_id.name or 'N/A'}

Reference: {self.name}

Please check the Portal for your updated schedule."""

    def _get_reminder_message(self):
        """Build 24-hour reminder message."""
        self.ensure_one()

        start_time = f"{int(self.start_time):02d}:{int((self.start_time % 1) * 60):02d}" if self.start_time else "TBD"

        return f"""⏰ Reminder: Visit Tomorrow

Hello {self.partner_id.name},

Reminder of your scheduled visit:

📅 Tomorrow, {self.visit_date.strftime('%A %d/%m/%Y') if self.visit_date else 'TBD'}
⏰ {start_time}
🏢 {self.client_id.name or 'N/A'}
📍 {self.installation_id.address or ''}, {self.installation_id.city or ''}

Reference: {self.name}

Safe travels!"""

    def action_open_whatsapp_composer(self):
        """Open WhatsApp compose wizard."""
        self.ensure_one()

        if not self.partner_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Partner'),
                    'message': _('Please assign a partner before sending WhatsApp.'),
                    'type': 'warning',
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'name': _('Send WhatsApp'),
            'res_model': 'wfm.whatsapp.compose',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_visit_id': self.id,
                'default_partner_id': self.partner_id.id,
            }
        }

    def action_view_whatsapp_messages(self):
        """View all WhatsApp messages for this visit."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('WhatsApp Messages'),
            'res_model': 'wfm.whatsapp.message',
            'view_mode': 'list,form',
            'domain': [('visit_id', '=', self.id)],
            'context': {'default_visit_id': self.id},
        }

    @api.model
    def _send_24h_reminders(self):
        """Cron job: Send reminders for visits happening tomorrow.

        Called by scheduled action daily.
        """
        tomorrow = fields.Date.today() + timedelta(days=1)

        visits = self.search([
            ('visit_date', '=', tomorrow),
            ('state', 'in', ['assigned', 'confirmed']),
            ('partner_id', '!=', False),
        ])

        _logger.info(f"Sending 24h reminders for {len(visits)} visits")

        for visit in visits:
            # Check if reminder already sent
            existing = self.env['wfm.whatsapp.message'].search([
                ('visit_id', '=', visit.id),
                ('message_type', '=', 'reminder'),
                ('status', 'in', ['sent', 'delivered']),
            ], limit=1)

            if not existing:
                try:
                    visit._send_whatsapp_reminder()
                except Exception as e:
                    _logger.error(f"Failed to send reminder for visit {visit.name}: {e}")

        return True
