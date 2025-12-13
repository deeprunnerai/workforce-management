import logging
import os
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Twilio import with fallback
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    _logger.warning("Twilio library not installed. WhatsApp notifications disabled.")


class WfmWhatsAppMessage(models.Model):
    """WhatsApp message log for WFM notifications."""

    _name = 'wfm.whatsapp.message'
    _description = 'WhatsApp Message'
    _order = 'sent_at desc, id desc'
    _rec_name = 'display_name'

    # Relations
    visit_id = fields.Many2one(
        'wfm.visit',
        string='Visit',
        ondelete='cascade',
        index=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Recipient',
        required=True,
        index=True
    )

    # Message details
    phone = fields.Char(
        string='Phone Number',
        required=True,
        help='WhatsApp number in format +countrycode...'
    )
    message_type = fields.Selection([
        ('assignment', 'Assignment'),
        ('confirmed', 'Confirmation'),
        ('reminder', '24h Reminder'),
        ('cancelled', 'Cancellation'),
        ('custom', 'Custom Message'),
    ], string='Type', required=True, default='custom')

    message_body = fields.Text(
        string='Message',
        required=True
    )

    # Status tracking
    status = fields.Selection([
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ], string='Status', default='pending', required=True)

    twilio_sid = fields.Char(
        string='Twilio SID',
        readonly=True,
        help='Twilio message identifier'
    )
    sent_at = fields.Datetime(
        string='Sent At',
        readonly=True
    )
    error_message = fields.Text(
        string='Error',
        readonly=True
    )

    # Computed
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('partner_id', 'message_type', 'sent_at')
    def _compute_display_name(self):
        for rec in self:
            type_label = dict(self._fields['message_type'].selection).get(rec.message_type, '')
            partner = rec.partner_id.name or 'Unknown'
            rec.display_name = f"{type_label} to {partner}"

    def _get_twilio_client(self):
        """Get configured Twilio client."""
        if not TWILIO_AVAILABLE:
            raise UserError(_("Twilio library not installed. Run: pip install twilio"))

        account_sid = os.environ.get('TWILIO_ACCOUNT_SID') or \
                      self.env['ir.config_parameter'].sudo().get_param('wfm.twilio.account_sid')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN') or \
                     self.env['ir.config_parameter'].sudo().get_param('wfm.twilio.auth_token')

        if not account_sid or not auth_token:
            raise UserError(_("Twilio credentials not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."))

        return TwilioClient(account_sid, auth_token)

    def _get_whatsapp_from_number(self):
        """Get the WhatsApp sender number."""
        from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER') or \
                      self.env['ir.config_parameter'].sudo().get_param('wfm.twilio.whatsapp_number')
        if not from_number:
            from_number = '+14155238886'  # Twilio sandbox default
        return f"whatsapp:{from_number}"

    def _format_phone_whatsapp(self, phone):
        """Format phone number for WhatsApp."""
        if not phone:
            return None
        # Remove spaces and dashes
        phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        # Ensure starts with +
        if not phone.startswith('+'):
            # Default to Greece country code
            if phone.startswith('69'):  # Greek mobile
                phone = '+30' + phone
            else:
                phone = '+' + phone
        return f"whatsapp:{phone}"

    def action_send(self):
        """Send the WhatsApp message via Twilio."""
        self.ensure_one()

        if self.status == 'sent':
            raise UserError(_("Message already sent."))

        try:
            client = self._get_twilio_client()
            from_number = self._get_whatsapp_from_number()
            to_number = self._format_phone_whatsapp(self.phone)

            if not to_number:
                raise UserError(_("Invalid phone number."))

            _logger.info(f"Sending WhatsApp: {from_number} -> {to_number}")

            message = client.messages.create(
                body=self.message_body,
                from_=from_number,
                to=to_number
            )

            self.write({
                'status': 'sent',
                'twilio_sid': message.sid,
                'sent_at': fields.Datetime.now(),
                'error_message': False,
            })

            _logger.info(f"WhatsApp sent successfully. SID: {message.sid}")

            # Post to visit chatter if linked
            if self.visit_id:
                self.visit_id.message_post(
                    body=f"📱 WhatsApp sent to {self.partner_id.name}:<br/><i>{self.message_body[:100]}...</i>",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )

            return True

        except Exception as e:
            error_msg = str(e)
            _logger.error(f"WhatsApp send failed: {error_msg}")
            self.write({
                'status': 'failed',
                'error_message': error_msg,
            })
            return False

    @api.model
    def send_message(self, partner_id, message_body, message_type='custom', visit_id=None):
        """Create and send a WhatsApp message.

        Args:
            partner_id: res.partner record or ID
            message_body: Message text
            message_type: Type of message
            visit_id: Optional wfm.visit record or ID

        Returns:
            wfm.whatsapp.message record
        """
        if isinstance(partner_id, int):
            partner = self.env['res.partner'].browse(partner_id)
        else:
            partner = partner_id

        if not partner.phone and not partner.mobile:
            _logger.warning(f"Partner {partner.name} has no phone number")
            return False

        phone = partner.mobile or partner.phone

        # Create message record
        message = self.create({
            'partner_id': partner.id,
            'phone': phone,
            'message_body': message_body,
            'message_type': message_type,
            'visit_id': visit_id.id if hasattr(visit_id, 'id') else visit_id,
        })

        # Send immediately
        message.action_send()

        return message
