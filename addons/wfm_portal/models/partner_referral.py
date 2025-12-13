from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PartnerReferral(models.Model):
    """Partner Referral - allows partners to refer new candidates to GEP."""
    _name = 'wfm.partner.referral'
    _description = 'Partner Referral'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New'),
        copy=False
    )

    # Referring partner (the one making the referral)
    referring_partner_id = fields.Many2one(
        'res.partner',
        string='Referred By',
        required=True,
        default=lambda self: self._get_current_partner(),
        readonly=True,
        tracking=True
    )

    # Candidate details
    candidate_name = fields.Char(
        string='Candidate Name',
        required=True,
        tracking=True
    )
    candidate_email = fields.Char(
        string='Candidate Email',
        required=True,
        tracking=True
    )
    candidate_phone = fields.Char(
        string='Candidate Phone',
        tracking=True
    )
    candidate_specialty = fields.Selection([
        ('physician', 'Occupational Physician'),
        ('safety_engineer', 'Safety Engineer'),
        ('health_scientist', 'Health Scientist'),
        ('other', 'Other'),
    ], string='Specialty', required=True, tracking=True)

    candidate_city = fields.Char(
        string='City',
        help='City where the candidate is based'
    )

    # Education fields
    candidate_bachelors = fields.Char(
        string='Bachelor\'s Degree',
        help='Field of study for Bachelor\'s degree'
    )
    candidate_masters = fields.Char(
        string='Master\'s Degree',
        help='Field of study for Master\'s degree (if applicable)'
    )
    candidate_phd = fields.Char(
        string='PhD',
        help='Field of study for PhD (if applicable)'
    )

    # Resume
    candidate_resume = fields.Binary(
        string='Resume/CV',
        help='Upload candidate resume (PDF or DOC)'
    )
    candidate_resume_filename = fields.Char(
        string='Resume Filename'
    )

    candidate_experience = fields.Text(
        string='Work Experience',
        help='Brief description of candidate work experience'
    )
    candidate_certifications = fields.Text(
        string='Certifications & Licenses',
        help='Relevant certifications, licenses, or professional memberships'
    )
    referral_reason = fields.Text(
        string='Why Refer This Person?',
        help='Why do you think this candidate would be a good fit for GEP?'
    )

    # Status workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('meeting_scheduled', 'Meeting Scheduled'),
    ], string='Status', default='draft', required=True, tracking=True)

    # Coordinator handling the referral
    coordinator_id = fields.Many2one(
        'res.users',
        string='Assigned Coordinator',
        tracking=True
    )

    # Review details
    review_notes = fields.Text(
        string='Coordinator Notes',
        help='Internal notes from coordinator review'
    )
    rejection_reason = fields.Text(
        string='Rejection Reason'
    )

    # Meeting details (when accepted)
    meeting_date = fields.Datetime(
        string='Meeting Date',
        tracking=True
    )
    meeting_location = fields.Char(
        string='Meeting Location/Link'
    )

    # Dates
    submitted_date = fields.Datetime(
        string='Submitted Date',
        readonly=True
    )
    reviewed_date = fields.Datetime(
        string='Reviewed Date',
        readonly=True
    )

    def _get_current_partner(self):
        """Get the partner linked to current user."""
        user = self.env.user
        if user.partner_id:
            return user.partner_id.id
        return False

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence number on create."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wfm.partner.referral') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        """Submit referral for coordinator review."""
        self.ensure_one()
        if not self.candidate_name or not self.candidate_email:
            raise UserError(_('Please fill in candidate name and email before submitting.'))

        self.write({
            'state': 'submitted',
            'submitted_date': fields.Datetime.now(),
        })

        # Send email to coordinators
        self._send_coordinator_notification()

        # Post message
        self.message_post(
            body=_('Referral submitted by %s for candidate %s') % (
                self.referring_partner_id.name,
                self.candidate_name
            ),
            message_type='notification'
        )

    def _send_coordinator_notification(self):
        """Send email notification to coordinators about new referral."""
        self.ensure_one()

        # Just send to admin email for now
        coordinator_emails = self.env.company.email or 'admin@gepgroup.gr'

        specialty_label = dict(self._fields['candidate_specialty'].selection).get(self.candidate_specialty, self.candidate_specialty)

        mail_values = {
            'subject': _('New Partner Referral: %s (%s)') % (self.candidate_name, specialty_label),
            'email_from': self.env.company.email or 'mailer@deeprunner.ai',
            'email_to': coordinator_emails,
            'body_html': f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">New Partner Referral Submitted</h2>

                <p>A new referral has been submitted and requires your review.</p>

                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #495057;">Candidate Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px 0; font-weight: bold;">Name:</td><td>{self.candidate_name}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Email:</td><td>{self.candidate_email}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Phone:</td><td>{self.candidate_phone or 'N/A'}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">Specialty:</td><td>{specialty_label}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">City:</td><td>{self.candidate_city or 'N/A'}</td></tr>
                    </table>
                </div>

                <div style="background-color: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #495057;">Referred By</h3>
                    <p><strong>{self.referring_partner_id.name}</strong></p>
                    <p><em>"{self.referral_reason or 'No reason provided'}"</em></p>
                </div>

                <p>Please log in to review this referral.</p>

                <p style="color: #7f8c8d; font-size: 12px;">
                    Reference: {self.name}<br/>
                    GEP Workforce Management System
                </p>
            </div>
            """,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()

    def action_start_review(self):
        """Coordinator starts reviewing the referral."""
        self.ensure_one()
        self.write({
            'state': 'under_review',
            'coordinator_id': self.env.user.id,
        })

    def action_accept(self):
        """Accept the referral and send meeting invitation."""
        self.ensure_one()
        if not self.meeting_date:
            raise UserError(_('Please set a meeting date before accepting.'))

        self.write({
            'state': 'accepted',
            'reviewed_date': fields.Datetime.now(),
        })

        # Send email to candidate
        self._send_meeting_invitation()

        # Post message
        self.message_post(
            body=_('Referral accepted! Meeting invitation sent to %s at %s') % (
                self.candidate_email,
                self.meeting_date.strftime('%Y-%m-%d %H:%M')
            ),
            message_type='notification'
        )

    def action_reject(self):
        """Reject the referral."""
        self.ensure_one()
        self.write({
            'state': 'rejected',
            'reviewed_date': fields.Datetime.now(),
        })

        self.message_post(
            body=_('Referral rejected. Reason: %s') % (self.rejection_reason or 'Not specified'),
            message_type='notification'
        )

    def action_mark_meeting_scheduled(self):
        """Mark that meeting has been scheduled/confirmed."""
        self.ensure_one()
        self.write({'state': 'meeting_scheduled'})

    def _send_meeting_invitation(self):
        """Send email invitation to the candidate."""
        self.ensure_one()

        # Get email template or send direct
        template = self.env.ref('wfm_portal.email_template_referral_meeting', raise_if_not_found=False)

        if template:
            template.send_mail(self.id, force_send=True)
        else:
            # Send direct email
            mail_values = {
                'subject': _('Interview Invitation - GEP OHS Partner Opportunity'),
                'email_from': self.env.company.email or 'noreply@gepgroup.gr',
                'email_to': self.candidate_email,
                'body_html': self._get_meeting_email_body(),
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()

    def _get_meeting_email_body(self):
        """Generate email body for meeting invitation."""
        meeting_time = self.meeting_date.strftime('%A, %B %d, %Y at %H:%M') if self.meeting_date else 'TBD'
        location = self.meeting_location or 'To be confirmed'

        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">Interview Invitation - GEP Group</h2>

            <p>Dear {self.candidate_name},</p>

            <p>Thank you for your interest in joining the GEP OHS partner network!</p>

            <p>You have been referred by <strong>{self.referring_partner_id.name}</strong>, one of our valued partners.
            We would like to invite you for an interview to discuss potential collaboration opportunities.</p>

            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #495057;">Meeting Details</h3>
                <p><strong>Date & Time:</strong> {meeting_time}</p>
                <p><strong>Location:</strong> {location}</p>
            </div>

            <p>Please reply to confirm your attendance or suggest an alternative time if needed.</p>

            <p>We look forward to meeting you!</p>

            <p>Best regards,<br>
            <strong>GEP Group - Workforce Management Team</strong><br>
            Greece's Leading OHS Service Provider</p>
        </div>
        """

    def action_reset_to_draft(self):
        """Reset to draft state."""
        self.ensure_one()
        self.write({'state': 'draft'})

    def action_send_meeting_invitation(self):
        """Resend meeting invitation email."""
        self.ensure_one()
        if self.state not in ('accepted', 'meeting_scheduled'):
            raise UserError(_('Can only send invitation for accepted referrals.'))
        if not self.meeting_date:
            raise UserError(_('Please set a meeting date first.'))
        self._send_meeting_invitation()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Email Sent'),
                'message': _('Meeting invitation has been sent to %s') % self.candidate_email,
                'sticky': False,
                'type': 'success',
            }
        }
