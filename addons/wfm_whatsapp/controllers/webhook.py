import logging
import hashlib
import hmac
import os

from odoo import http, SUPERUSER_ID
from odoo.http import request

_logger = logging.getLogger(__name__)


class WhatsAppWebhook(http.Controller):
    """Webhook controller for Twilio WhatsApp incoming messages.

    Webhook URL to configure in Twilio:
    https://odoo.deeprunner.ai/whatsapp/webhook

    Supported commands:
    - ACCEPT / YES / OK - Confirm assigned visit
    - DENY / NO / CANCEL - Decline assigned visit
    - help - Get help information
    - visits - List upcoming visits
    - visit N - Get details for visit N
    - status - Check visit status
    """

    @http.route('/whatsapp/webhook', type='http', auth='public',
                methods=['POST'], csrf=False)
    def whatsapp_webhook(self, **kwargs):
        """Handle incoming WhatsApp messages from Twilio.

        Twilio sends POST with:
        - From: whatsapp:+phonenumber
        - Body: message text
        - MessageSid: unique message ID
        """
        try:
            # Parse Twilio webhook data
            from_number = kwargs.get('From', '')
            message_body = kwargs.get('Body', '').strip()
            message_sid = kwargs.get('MessageSid', '')

            _logger.info(f"WhatsApp webhook received: From={from_number}, Body={message_body[:50]}")

            if not from_number or not message_body:
                return self._twiml_response("Invalid request")

            # Extract phone number (remove 'whatsapp:' prefix)
            phone = from_number.replace('whatsapp:', '').strip()

            # Process with sudo to bypass access rights
            env = request.env(user=SUPERUSER_ID)

            # Find partner by phone
            partner = self._find_partner_by_phone(env, phone)

            if not partner:
                _logger.warning(f"No partner found for phone: {phone}")
                return self._twiml_response(
                    "Sorry, we couldn't identify your account. "
                    "Please contact GEP support."
                )

            # Log incoming message
            self._log_incoming_message(env, partner, phone, message_body, message_sid)

            # Process command
            response = self._process_message(env, partner, message_body.upper())

            return self._twiml_response(response)

        except Exception as e:
            _logger.exception(f"WhatsApp webhook error: {e}")
            return self._twiml_response(
                "Sorry, an error occurred. Please try again or contact support."
            )

    def _twiml_response(self, message):
        """Generate TwiML response for Twilio."""
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message}</Message>
</Response>"""
        return request.make_response(
            twiml,
            headers=[('Content-Type', 'text/xml')]
        )

    def _find_partner_by_phone(self, env, phone):
        """Find partner by phone number (various formats)."""
        # Normalize phone for search
        phone_clean = phone.replace('+', '').replace(' ', '').replace('-', '')

        # Ensure phone has + prefix for sanitized search
        phone_with_plus = '+' + phone_clean if not phone.startswith('+') else phone.replace(' ', '')

        # Try different search patterns
        Partner = env['res.partner'].sudo()

        # First try phone_sanitized field (most reliable)
        partner = Partner.search([
            '|',
            ('phone_sanitized', '=', phone_with_plus),
            ('phone_sanitized', 'ilike', phone_clean[-10:]),  # Last 10 digits
        ], limit=1)

        if not partner:
            # Fallback to phone field
            partner = Partner.search([
                '|',
                ('phone', 'ilike', phone),
                ('phone', 'ilike', phone_clean[-10:]),
            ], limit=1)

        if not partner:
            # Try with country code variations (Greece)
            if phone_clean.startswith('30'):
                local = phone_clean[2:]
                partner = Partner.search([
                    ('phone_sanitized', 'ilike', local),
                ], limit=1)

        return partner

    def _log_incoming_message(self, env, partner, phone, message_body, message_sid):
        """Log incoming WhatsApp message."""
        env['wfm.whatsapp.message'].sudo().create({
            'partner_id': partner.id,
            'phone': phone,
            'message_body': f"[INCOMING] {message_body}",
            'message_type': 'custom',
            'status': 'delivered',
            'twilio_sid': message_sid,
            'sent_at': False,  # Incoming, not sent
        })

    def _process_message(self, env, partner, message):
        """Process incoming message and return response."""
        message_raw = message.strip()
        message = message_raw.upper()

        # Handle help command
        if message in ['HELP', '?']:
            return self._handle_help(env, partner)

        # Handle visits command
        if message in ['VISITS', 'UPCOMING']:
            return self._handle_visits_list(env, partner)

        # Handle visit N command (e.g., visit 1, visit 2)
        if message.startswith('VISIT '):
            parts = message.split()
            if len(parts) >= 2 and parts[1].isdigit():
                return self._handle_visit_detail(env, partner, int(parts[1]))

        # Handle status command
        if message in ['STATUS']:
            return self._handle_status(env, partner)

        # Handle ACCEPT variations
        if message in ['ACCEPT', 'YES', 'OK', 'CONFIRM', 'SI', 'ΝΑΙ', 'ΔΕΧΟΜΑΙ']:
            return self._handle_accept(env, partner)

        # Handle DENY variations
        if message in ['DENY', 'NO', 'CANCEL', 'REJECT', 'ΟΧΙ', 'ΑΡΝΟΥΜΑΙ']:
            return self._handle_deny(env, partner)

        # Unknown command - show help
        return self._handle_unknown(env, partner, message)

    def _handle_help(self, env, partner):
        """Handle help command."""
        return """🏥 *GEP OHS Partner Help*

Available commands:

📋 *Visit Management:*
• ACCEPT - Confirm your assigned visit
• DENY - Decline the assigned visit

📊 *Information:*
• visits - See your upcoming visits
• visit 1 - Get details of visit #1
• status - Check current visit status
• help - Show this help message

💡 *Tips:*
• Reply ACCEPT or DENY after receiving an assignment
• Use visit 1, visit 2 etc. for full details with map
• Contact your coordinator for schedule changes

Need assistance? Contact GEP support."""

    def _handle_visits_list(self, env, partner):
        """Handle visits command - list upcoming visits."""
        Visit = env['wfm.visit'].sudo()

        visits = Visit.search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['assigned', 'confirmed']),
        ], order='visit_date asc', limit=5)

        if not visits:
            return "📋 You have no upcoming visits assigned.\n\nCheck the Partner Portal for updates."

        response = "📋 *Your Upcoming Visits:*\n\n"

        for i, visit in enumerate(visits, 1):
            date_str = visit.visit_date.strftime('%d/%m/%Y') if visit.visit_date else 'TBD'
            time_str = f"{int(visit.start_time):02d}:{int((visit.start_time % 1) * 60):02d}" if visit.start_time else 'TBD'
            status = '✅' if visit.state == 'confirmed' else '⏳'

            response += f"{status} *{i}. {visit.name}*\n"
            response += f"   📅 {date_str} at {time_str}\n"
            response += f"   🏢 {visit.client_id.name or 'N/A'}\n\n"

        response += "━━━━━━━━━━━━━━━━━━━━━\n"
        response += "💡 Reply *visit 1* for full details with map"

        return response

    def _get_google_maps_url(self, installation):
        """Generate Google Maps URL for an installation."""
        if not installation:
            return None

        # Build address string
        address_parts = []
        if installation.street:
            address_parts.append(installation.street)
        if installation.city:
            address_parts.append(installation.city)
        if hasattr(installation, 'postal_code') and installation.postal_code:
            address_parts.append(installation.postal_code)
        if hasattr(installation, 'country_id') and installation.country_id:
            address_parts.append(installation.country_id.name)

        if not address_parts:
            return None

        import urllib.parse
        address = ', '.join(address_parts)
        encoded_address = urllib.parse.quote(address)
        return f"https://www.google.com/maps/search/?api=1&query={encoded_address}"

    def _handle_visit_detail(self, env, partner, visit_number):
        """Handle visit N command - show detailed visit info."""
        Visit = env['wfm.visit'].sudo()

        visits = Visit.search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['assigned', 'confirmed']),
        ], order='visit_date asc', limit=10)

        if not visits:
            return "📋 You have no upcoming visits assigned."

        if visit_number < 1 or visit_number > len(visits):
            return f"❌ Invalid visit number. You have {len(visits)} upcoming visit(s).\n\nType *visits* to see the list."

        visit = visits[visit_number - 1]

        # Format date and time
        date_str = visit.visit_date.strftime('%A, %d %B %Y') if visit.visit_date else 'TBD'
        start_time = f"{int(visit.start_time):02d}:{int((visit.start_time % 1) * 60):02d}" if visit.start_time else 'TBD'
        end_time = f"{int(visit.end_time):02d}:{int((visit.end_time % 1) * 60):02d}" if visit.end_time else 'TBD'
        duration = f"{visit.duration:.1f}" if visit.duration else 'N/A'
        status = '✅ Confirmed' if visit.state == 'confirmed' else '⏳ Awaiting Confirmation'

        # Build address
        address_lines = []
        if visit.installation_id:
            inst = visit.installation_id
            if inst.name:
                address_lines.append(inst.name)
            if inst.street:
                address_lines.append(inst.street)
            if inst.city:
                city_line = inst.city
                if hasattr(inst, 'postal_code') and inst.postal_code:
                    city_line = f"{inst.postal_code} {city_line}"
                address_lines.append(city_line)

        address_text = '\n   '.join(address_lines) if address_lines else 'Address not specified'

        # Get Google Maps URL
        maps_url = self._get_google_maps_url(visit.installation_id)

        response = f"""📋 *Visit Details #{visit_number}*

━━━━━━━━━━━━━━━━━━━━━
📌 *VISIT INFORMATION*
━━━━━━━━━━━━━━━━━━━━━

🔖 *Reference:* {visit.name}
📊 *Status:* {status}
📅 *Date:* {date_str}
⏰ *Time:* {start_time} - {end_time}
⏱️ *Duration:* {duration} hours

━━━━━━━━━━━━━━━━━━━━━
🏢 *CLIENT & LOCATION*
━━━━━━━━━━━━━━━━━━━━━

🏛️ *Client:* {visit.client_id.name or 'N/A'}
📍 *Location:*
   {address_text}"""

        if maps_url:
            response += f"""

🗺️ *Navigate:*
{maps_url}"""

        if visit.state == 'assigned':
            response += """

━━━━━━━━━━━━━━━━━━━━━
Reply *ACCEPT* to confirm or *DENY* to decline."""

        return response

    def _handle_status(self, env, partner):
        """Handle status command - show current assignment status."""
        Visit = env['wfm.visit'].sudo()

        # Find most recent assigned visit
        visit = Visit.search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'assigned'),
        ], order='create_date desc', limit=1)

        if not visit:
            # Check for confirmed
            visit = Visit.search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'confirmed'),
            ], order='visit_date asc', limit=1)

            if visit:
                return f"""✅ *Visit Status: CONFIRMED*

🔖 Reference: {visit.name}
📅 Date: {visit.visit_date.strftime('%d/%m/%Y') if visit.visit_date else 'TBD'}
🏢 Client: {visit.client_id.name or 'N/A'}

Your visit is confirmed. See you there!"""

        if not visit:
            return "📋 No pending visits require your attention.\n\nType *visits* to see your schedule."

        return f"""⏳ *Visit Status: AWAITING CONFIRMATION*

🔖 Reference: {visit.name}
📅 Date: {visit.visit_date.strftime('%d/%m/%Y') if visit.visit_date else 'TBD'}
🏢 Client: {visit.client_id.name or 'N/A'}

Reply *ACCEPT* to confirm or *DENY* to decline."""

    def _handle_accept(self, env, partner):
        """Handle ACCEPT command - confirm the latest assigned visit."""
        Visit = env['wfm.visit'].sudo()

        # Find the most recent assigned (not yet confirmed) visit
        visit = Visit.search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'assigned'),
        ], order='create_date desc', limit=1)

        if not visit:
            return "ℹ️ No pending visit assignments found.\n\nType *visits* to see your schedule."

        try:
            # Confirm the visit
            visit.write({'state': 'confirmed'})

            # Log the confirmation
            visit.message_post(
                body=f"✅ Partner confirmed via WhatsApp",
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

            _logger.info(f"Visit {visit.name} confirmed by {partner.name} via WhatsApp")

            date_str = visit.visit_date.strftime('%A, %d %B %Y') if visit.visit_date else 'TBD'
            time_str = f"{int(visit.start_time):02d}:{int((visit.start_time % 1) * 60):02d}" if visit.start_time else 'TBD'

            return f"""✅ *Visit Confirmed!*

Thank you for confirming your visit:

🔖 Reference: {visit.name}
📅 Date: {date_str}
⏰ Time: {time_str}
🏢 Client: {visit.client_id.name or 'N/A'}

See you there! Safe travels. 🚗"""

        except Exception as e:
            _logger.error(f"Error confirming visit {visit.name}: {e}")
            return "❌ Error confirming visit. Please try again or contact your coordinator."

    def _handle_deny(self, env, partner):
        """Handle DENY command - decline the latest assigned visit."""
        Visit = env['wfm.visit'].sudo()

        # Find the most recent assigned visit
        visit = Visit.search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'assigned'),
        ], order='create_date desc', limit=1)

        if not visit:
            return "ℹ️ No pending visit assignments found.\n\nType *visits* to see your schedule."

        try:
            # Reset the assignment (remove partner, back to draft)
            visit.write({
                'partner_id': False,
                'state': 'draft',
            })

            # Log the decline
            visit.message_post(
                body=f"❌ Partner {partner.name} declined via WhatsApp. Visit returned to draft.",
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

            _logger.info(f"Visit {visit.name} declined by {partner.name} via WhatsApp")

            return f"""❌ *Visit Declined*

You have declined the following visit:

🔖 Reference: {visit.name}
📅 Date: {visit.visit_date.strftime('%d/%m/%Y') if visit.visit_date else 'TBD'}
🏢 Client: {visit.client_id.name or 'N/A'}

The coordinator will assign another partner.

If this was a mistake, please contact your coordinator immediately."""

        except Exception as e:
            _logger.error(f"Error declining visit {visit.name}: {e}")
            return "❌ Error processing decline. Please try again or contact your coordinator."

    def _handle_unknown(self, env, partner, message):
        """Handle unknown command."""
        return f"""🤔 Command not recognized: "{message[:20]}"

Reply with:
• *ACCEPT* - To confirm a visit
• *DENY* - To decline a visit
• *help* - For more options"""

    @http.route('/whatsapp/status', type='http', auth='public',
                methods=['POST'], csrf=False)
    def whatsapp_status_callback(self, **kwargs):
        """Handle Twilio status callbacks for message delivery tracking.

        Configure as Status Callback URL in Twilio.
        """
        try:
            message_sid = kwargs.get('MessageSid')
            message_status = kwargs.get('MessageStatus')

            _logger.info(f"WhatsApp status update: SID={message_sid}, Status={message_status}")

            if message_sid and message_status:
                env = request.env(user=SUPERUSER_ID)
                message = env['wfm.whatsapp.message'].sudo().search([
                    ('twilio_sid', '=', message_sid)
                ], limit=1)

                if message:
                    status_map = {
                        'queued': 'pending',
                        'sent': 'sent',
                        'delivered': 'delivered',
                        'read': 'read',
                        'failed': 'failed',
                        'undelivered': 'failed',
                    }
                    new_status = status_map.get(message_status, message.status)
                    message.write({'status': new_status})

            return "OK"

        except Exception as e:
            _logger.exception(f"WhatsApp status callback error: {e}")
            return "Error"
