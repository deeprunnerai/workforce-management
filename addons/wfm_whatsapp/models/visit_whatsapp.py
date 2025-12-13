import logging
import urllib.parse
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

    def _get_google_maps_url(self):
        """Generate Google Maps URL for the installation address."""
        self.ensure_one()
        if not self.installation_id:
            return None

        # Build address string
        address_parts = []
        if self.installation_id.street:
            address_parts.append(self.installation_id.street)
        if self.installation_id.city:
            address_parts.append(self.installation_id.city)
        if self.installation_id.postal_code:
            address_parts.append(self.installation_id.postal_code)
        if self.installation_id.country_id:
            address_parts.append(self.installation_id.country_id.name)

        if not address_parts:
            return None

        address = ', '.join(address_parts)
        encoded_address = urllib.parse.quote(address)
        return f"https://www.google.com/maps/search/?api=1&query={encoded_address}"

    def _format_time(self, time_float):
        """Format float time to HH:MM string."""
        if not time_float:
            return "TBD"
        hours = int(time_float)
        minutes = int((time_float % 1) * 60)
        return f"{hours:02d}:{minutes:02d}"

    def _get_assignment_message(self):
        """Build assignment notification message with full details."""
        self.ensure_one()

        start_time = self._format_time(self.start_time)
        end_time = self._format_time(self.end_time)
        maps_url = self._get_google_maps_url()

        # Build full address
        address_lines = []
        if self.installation_id.name:
            address_lines.append(self.installation_id.name)
        if self.installation_id.street:
            address_lines.append(self.installation_id.street)
        if self.installation_id.city:
            city_line = self.installation_id.city
            if self.installation_id.postal_code:
                city_line = f"{self.installation_id.postal_code} {city_line}"
            address_lines.append(city_line)

        address_text = '\n   '.join(address_lines) if address_lines else 'Address not specified'

        message = f"""🏥 *GEP OHS - New Visit Assignment*

Hello {self.partner_id.name},

You have been assigned to a new OHS visit. Please review the details below:

━━━━━━━━━━━━━━━━━━━━━
📋 *VISIT DETAILS*
━━━━━━━━━━━━━━━━━━━━━

🔖 *Reference:* {self.name}
📅 *Date:* {self.visit_date.strftime('%A, %d %B %Y') if self.visit_date else 'TBD'}
⏰ *Time:* {start_time} - {end_time}
⏱️ *Duration:* {self.duration:.1f} hours

━━━━━━━━━━━━━━━━━━━━━
🏢 *CLIENT INFORMATION*
━━━━━━━━━━━━━━━━━━━━━

🏛️ *Client:* {self.client_id.name or 'N/A'}
📍 *Location:*
   {address_text}"""

        if maps_url:
            message += f"""

🗺️ *Google Maps:*
{maps_url}"""

        message += f"""

━━━━━━━━━━━━━━━━━━━━━
✅ *CONFIRM YOUR AVAILABILITY*
━━━━━━━━━━━━━━━━━━━━━

Please reply with:
👍 *ACCEPT* - To confirm this visit
👎 *DENY* - If you cannot attend

Or contact your coordinator for any questions."""

        return message

    def _get_confirmed_message(self):
        """Build confirmation acknowledgment message."""
        self.ensure_one()

        start_time = self._format_time(self.start_time)
        end_time = self._format_time(self.end_time)
        maps_url = self._get_google_maps_url()

        # Build address
        address_parts = []
        if self.installation_id.street:
            address_parts.append(self.installation_id.street)
        if self.installation_id.city:
            address_parts.append(self.installation_id.city)
        address_text = ', '.join(address_parts) if address_parts else 'See details below'

        message = f"""✅ *Visit Confirmed*

Thank you! Your visit has been confirmed.

━━━━━━━━━━━━━━━━━━━━━
📋 *CONFIRMED VISIT*
━━━━━━━━━━━━━━━━━━━━━

🔖 *Reference:* {self.name}
📅 *Date:* {self.visit_date.strftime('%A, %d %B %Y') if self.visit_date else 'TBD'}
⏰ *Time:* {start_time} - {end_time}
🏛️ *Client:* {self.client_id.name or 'N/A'}
📍 *Location:* {address_text}"""

        if maps_url:
            message += f"""

🗺️ *Navigate:*
{maps_url}"""

        message += """

━━━━━━━━━━━━━━━━━━━━━
See you there! Safe travels. 🚗"""

        return message

    def _get_cancelled_message(self):
        """Build cancellation notice message."""
        self.ensure_one()

        return f"""❌ *Visit Cancelled*

The following visit has been cancelled:

━━━━━━━━━━━━━━━━━━━━━
📋 *CANCELLED VISIT*
━━━━━━━━━━━━━━━━━━━━━

🔖 *Reference:* {self.name}
📅 *Date:* {self.visit_date.strftime('%A, %d %B %Y') if self.visit_date else 'TBD'}
🏛️ *Client:* {self.client_id.name or 'N/A'}

━━━━━━━━━━━━━━━━━━━━━

Please check the Partner Portal for your updated schedule.

If you have questions, contact your coordinator."""

    def _get_reminder_message(self):
        """Build 24-hour reminder message."""
        self.ensure_one()

        start_time = self._format_time(self.start_time)
        end_time = self._format_time(self.end_time)
        maps_url = self._get_google_maps_url()

        # Build address
        address_parts = []
        if self.installation_id.street:
            address_parts.append(self.installation_id.street)
        if self.installation_id.city:
            address_parts.append(self.installation_id.city)
        address_text = ', '.join(address_parts) if address_parts else 'See navigation link'

        message = f"""⏰ *Reminder: Visit Tomorrow*

Hello {self.partner_id.name},

This is a friendly reminder about your scheduled visit tomorrow.

━━━━━━━━━━━━━━━━━━━━━
📋 *VISIT DETAILS*
━━━━━━━━━━━━━━━━━━━━━

🔖 *Reference:* {self.name}
📅 *Date:* Tomorrow, {self.visit_date.strftime('%A %d %B %Y') if self.visit_date else 'TBD'}
⏰ *Time:* {start_time} - {end_time}
🏛️ *Client:* {self.client_id.name or 'N/A'}
📍 *Location:* {address_text}"""

        if maps_url:
            message += f"""

🗺️ *Navigate:*
{maps_url}"""

        message += """

━━━━━━━━━━━━━━━━━━━━━
Safe travels! 🚗"""

        return message

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
