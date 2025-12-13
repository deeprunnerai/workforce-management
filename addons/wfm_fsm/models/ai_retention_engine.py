import json
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# LiteLLM/Claude Configuration
LITELLM_API_KEY = "sk-nJE8QNo249xmGq1KMFJAIw"
LITELLM_BASE_URL = "https://prod.litellm.deeprunner.ai"
CLAUDE_MODEL = "claude-3-5-haiku-latest"


class AIRetentionEngine(models.Model):
    """
    AI-powered Partner Retention Engine using Claude.

    Analyzes partner data holistically and generates:
    - Personalized retention strategies
    - Ready-to-send WhatsApp messages
    - Specific action recommendations with reasoning
    """
    _name = 'wfm.ai.retention.engine'
    _description = 'AI Retention Engine'

    name = fields.Char(default='AI Retention Engine')

    def _get_claude_client(self):
        """Initialize OpenAI client for Claude via LiteLLM"""
        try:
            import openai
            return openai.OpenAI(
                api_key=LITELLM_API_KEY,
                base_url=LITELLM_BASE_URL
            )
        except ImportError:
            _logger.error("OpenAI package not installed. Run: pip install openai")
            return None

    def _gather_partner_context(self, partner_health):
        """
        Gather comprehensive context about a partner for AI analysis.
        Returns a structured dict with all relevant data.
        """
        partner = partner_health.partner_id

        # Get visit history
        visits = self.env['wfm.visit'].search([
            ('partner_id', '=', partner.id)
        ], order='visit_date desc', limit=20)

        visit_summary = []
        for v in visits:
            visit_summary.append({
                'date': str(v.visit_date),
                'client': v.client_id.name if v.client_id else 'Unknown',
                'status': v.state,
                'cancelled': v.state == 'cancelled',
            })

        # Get past interventions
        interventions = self.env['wfm.partner.intervention'].search([
            ('partner_id', '=', partner.id)
        ], order='date desc', limit=5)

        intervention_history = []
        for i in interventions:
            intervention_history.append({
                'date': str(i.date),
                'type': dict(i._fields['intervention_type'].selection).get(i.intervention_type),
                'outcome': dict(i._fields['outcome'].selection).get(i.outcome),
                'notes': i.notes or '',
            })

        # Get relationship data
        relationships = self.env['wfm.partner.client.relationship'].search([
            ('partner_id', '=', partner.id)
        ], order='relationship_score desc', limit=5)

        top_clients = []
        for r in relationships:
            top_clients.append({
                'client': r.client_id.name,
                'total_visits': r.total_visits,
                'score': r.relationship_score,
            })

        return {
            'partner': {
                'name': partner.name,
                'specialty': partner.specialty if hasattr(partner, 'specialty') else 'Unknown',
                'city': partner.city or 'Unknown',
                'phone': partner.phone or partner.mobile or 'No phone',
                'email': partner.email or 'No email',
            },
            'health_metrics': {
                'risk_score': partner_health.churn_risk_score,
                'risk_level': partner_health.risk_level,
                'visits_last_30d': partner_health.visits_last_30d,
                'visits_previous_30d': partner_health.visits_previous_30d,
                'visits_declined': partner_health.visits_declined_30d,
                'days_since_last_visit': partner_health.days_since_last_visit,
                'decline_rate_score': partner_health.decline_rate_score,
                'inactivity_score': partner_health.inactivity_score,
                'volume_change_score': partner_health.volume_change_score,
                'payment_issue_score': partner_health.payment_issue_score,
            },
            'recent_visits': visit_summary[:10],
            'past_interventions': intervention_history,
            'top_client_relationships': top_clients,
        }

    def analyze_partner_and_generate_outreach(self, partner_health_id):
        """
        Main method: Analyze partner and generate personalized retention strategy.

        Returns dict with:
        - analysis: AI's understanding of the situation
        - risk_factors: Key reasons for churn risk
        - recommended_action: What to do
        - whatsapp_message: Ready-to-send Greek message
        - email_subject: Email subject line
        - email_body: Email content
        """
        partner_health = self.env['wfm.partner.health'].browse(partner_health_id)
        if not partner_health.exists():
            return {'error': 'Partner health record not found'}

        # Gather all context
        context = self._gather_partner_context(partner_health)

        # Build the prompt
        prompt = self._build_retention_prompt(context)

        # Call Claude
        client = self._get_claude_client()
        if not client:
            return {'error': 'Could not initialize AI client'}

        try:
            response = client.chat.completions.create(
                model=CLAUDE_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert retention specialist for GEP Group, Greece's largest Occupational Health & Safety (OHS) service provider.

Your job is to analyze partner (external contractor) data and create personalized retention strategies. Partners are physicians and safety engineers who conduct OHS visits for GEP's clients.

You must respond in JSON format with these exact keys:
- analysis: Your understanding of why this partner might leave (2-3 sentences)
- risk_factors: Array of specific risk factors identified
- recommended_action: The single best action to take right now
- urgency: "immediate", "this_week", or "monitor"
- whatsapp_message: A warm, personalized WhatsApp message in GREEK to re-engage them (use their name, reference specific data)
- email_subject: Email subject line in Greek
- email_body: Full email body in Greek (professional but warm)
- talking_points: Array of 3-4 points for a phone call

Keep messages genuine, not salesy. Reference specific data points to show you understand their situation."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )

            # Parse response
            ai_response = response.choices[0].message.content

            # Try to parse as JSON
            try:
                # Handle potential markdown code blocks
                if '```json' in ai_response:
                    ai_response = ai_response.split('```json')[1].split('```')[0]
                elif '```' in ai_response:
                    ai_response = ai_response.split('```')[1].split('```')[0]

                result = json.loads(ai_response.strip())
                result['success'] = True
                result['partner_name'] = context['partner']['name']
                result['risk_score'] = context['health_metrics']['risk_score']
                return result
            except json.JSONDecodeError:
                # Return raw response if JSON parsing fails
                return {
                    'success': True,
                    'raw_response': ai_response,
                    'partner_name': context['partner']['name'],
                }

        except Exception as e:
            _logger.error(f"AI retention analysis failed: {str(e)}")
            return {'error': str(e), 'success': False}

    def _build_retention_prompt(self, context):
        """Build a detailed prompt for Claude with all partner context"""

        partner = context['partner']
        metrics = context['health_metrics']

        prompt = f"""Analyze this partner's situation and create a retention strategy:

## PARTNER PROFILE
- Name: {partner['name']}
- Specialty: {partner['specialty']}
- Location: {partner['city']}
- Contact: {partner['phone']}

## CHURN RISK METRICS
- Overall Risk Score: {metrics['risk_score']}/100 ({metrics['risk_level'].upper()})
- Visits last 30 days: {metrics['visits_last_30d']}
- Visits previous 30 days: {metrics['visits_previous_30d']}
- Visits declined/cancelled: {metrics['visits_declined']}
- Days since last completed visit: {metrics['days_since_last_visit']}

## RISK SCORE BREAKDOWN (what's driving the risk)
- Decline Rate Score: {metrics['decline_rate_score']}/30 (visits declined)
- Inactivity Score: {metrics['inactivity_score']}/20 (days inactive)
- Volume Change Score: {metrics['volume_change_score']}/25 (drop in visits)
- Payment Issue Score: {metrics['payment_issue_score']}/15 (payment complaints)

## RECENT VISIT HISTORY
"""
        for v in context['recent_visits'][:5]:
            status = "❌ CANCELLED" if v['cancelled'] else f"✓ {v['status']}"
            prompt += f"- {v['date']}: {v['client']} - {status}\n"

        if context['past_interventions']:
            prompt += "\n## PAST RETENTION ATTEMPTS\n"
            for i in context['past_interventions']:
                prompt += f"- {i['date']}: {i['type']} → {i['outcome']}\n"
                if i['notes']:
                    prompt += f"  Notes: {i['notes'][:100]}...\n"

        if context['top_client_relationships']:
            prompt += "\n## STRONGEST CLIENT RELATIONSHIPS\n"
            for r in context['top_client_relationships'][:3]:
                prompt += f"- {r['client']}: {r['total_visits']} visits (score: {r['score']})\n"

        prompt += """

Based on this data, provide your retention analysis and outreach messages.
Remember: Write WhatsApp and email messages in GREEK. Be genuine and reference specific data."""

        return prompt

    def generate_bulk_outreach(self, risk_level='critical'):
        """
        Generate outreach for all partners at a given risk level.
        Returns list of generated strategies.
        """
        health_records = self.env['wfm.partner.health'].search([
            ('risk_level', '=', risk_level),
            ('needs_intervention', '=', True),
        ])

        results = []
        for health in health_records:
            result = self.analyze_partner_and_generate_outreach(health.id)
            results.append(result)

        return results


class WfmPartnerHealthAI(models.Model):
    """Extend Partner Health with AI capabilities"""
    _inherit = 'wfm.partner.health'

    # AI-generated fields
    ai_analysis = fields.Text(string='AI Analysis', readonly=True)
    ai_whatsapp_message = fields.Text(string='AI WhatsApp Message', readonly=True)
    ai_recommended_action = fields.Char(string='AI Recommended Action', readonly=True)
    ai_urgency = fields.Selection([
        ('immediate', '🔴 Immediate'),
        ('this_week', '🟡 This Week'),
        ('monitor', '🟢 Monitor'),
    ], string='AI Urgency', readonly=True)
    ai_generated_date = fields.Datetime(string='AI Analysis Date', readonly=True)

    def action_generate_ai_retention_strategy(self):
        """Button action to generate AI retention strategy"""
        self.ensure_one()

        engine = self.env['wfm.ai.retention.engine'].create({})
        result = engine.analyze_partner_and_generate_outreach(self.id)

        if result.get('success'):
            self.write({
                'ai_analysis': result.get('analysis', ''),
                'ai_whatsapp_message': result.get('whatsapp_message', ''),
                'ai_recommended_action': result.get('recommended_action', ''),
                'ai_urgency': result.get('urgency', 'monitor'),
                'ai_generated_date': fields.Datetime.now(),
            })

            # Return action to show the result
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '🤖 AI Analysis Complete',
                    'message': f"Strategy generated for {self.partner_id.name}",
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'AI Analysis Failed',
                    'message': result.get('error', 'Unknown error'),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_send_ai_whatsapp(self):
        """Send the AI-generated WhatsApp message"""
        self.ensure_one()

        if not self.ai_whatsapp_message:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Message',
                    'message': 'Generate AI strategy first',
                    'type': 'warning',
                }
            }

        # Check if WhatsApp module exists and send
        if hasattr(self.partner_id, 'send_whatsapp_message'):
            self.partner_id.send_whatsapp_message(self.ai_whatsapp_message)

            # Log the intervention
            self.env['wfm.partner.intervention'].create({
                'health_id': self.id,
                'partner_id': self.partner_id.id,
                'intervention_type': 'other',
                'notes': f"AI-generated WhatsApp message sent:\n\n{self.ai_whatsapp_message}",
                'outcome': 'pending',
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '📱 WhatsApp Sent',
                    'message': f"Message sent to {self.partner_id.name}",
                    'type': 'success',
                }
            }
        else:
            # Open WhatsApp Web/App directly with pre-filled message
            import urllib.parse
            phone = self.partner_id.mobile or self.partner_id.phone
            if phone:
                # Clean phone number (remove spaces, dashes, etc.)
                clean_phone = ''.join(filter(str.isdigit, phone))
                # Add Greece country code if not present
                if not clean_phone.startswith('30') and len(clean_phone) == 10:
                    clean_phone = '30' + clean_phone

                # URL encode the message
                encoded_msg = urllib.parse.quote(self.ai_whatsapp_message)
                whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"

                # Log the intervention
                self.env['wfm.partner.intervention'].create({
                    'health_id': self.id,
                    'partner_id': self.partner_id.id,
                    'intervention_type': 'whatsapp',
                    'notes': f"AI-generated WhatsApp outreach:\n\n{self.ai_whatsapp_message}",
                    'outcome': 'pending',
                })

                return {
                    'type': 'ir.actions.act_url',
                    'url': whatsapp_url,
                    'target': 'new',
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'No Phone Number',
                        'message': f"{self.partner_id.name} has no phone number configured",
                        'type': 'warning',
                    }
                }
