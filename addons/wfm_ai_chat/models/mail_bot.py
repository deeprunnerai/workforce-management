import logging
import html

from markupsafe import Markup
from odoo import models, api

_logger = logging.getLogger(__name__)

# Maximum number of messages to include in conversation history
MAX_HISTORY_MESSAGES = 10


class MailBotAI(models.AbstractModel):
    """Override mail.bot to use LLM for intelligent responses."""

    _inherit = 'mail.bot'

    def _get_answer(self, channel, body, values, command=False):
        """
        Override to use LLM for answering user queries.

        Activates when:
        - Direct chat with OdooBot (user in 'idle' state)
        - Group/channel where @OdooBot is mentioned
        """
        odoobot = self.env.ref("base.partner_root")
        odoobot_state = self.env.user.odoobot_state

        # Check if this is a direct chat with OdooBot
        is_direct_odoobot_chat = (
            channel.channel_type == "chat" and
            odoobot in channel.channel_member_ids.partner_id
        )

        # Check if OdooBot is mentioned in a group/channel
        # The mention format in Odoo is typically @OdooBot or contains partner_root reference
        is_mentioned_in_group = (
            channel.channel_type in ("group", "channel") and
            odoobot in channel.channel_member_ids.partner_id and
            self._is_odoobot_mentioned(body, odoobot)
        )

        # Only proceed if it's a direct chat OR mentioned in group
        if not is_direct_odoobot_chat and not is_mentioned_in_group:
            return super()._get_answer(channel, body, values, command)

        # Handle onboarding states normally (only for direct chats)
        if is_direct_odoobot_chat and odoobot_state not in (False, 'idle', 'not_initialized'):
            return super()._get_answer(channel, body, values, command)

        # Check if user wants to start the tour (let original handler deal with it)
        if 'start the tour' in body.lower():
            return super()._get_answer(channel, body, values, command)

        # Clean the message body (remove @OdooBot mention for cleaner processing)
        clean_body = self._clean_mention(body, odoobot)

        # Check if LLM is configured
        ICP = self.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('wfm_ai_chat.litellm_api_key', '')

        if not api_key:
            # LLM not configured, fall back to default behavior
            return super()._get_answer(channel, body, values, command)

        # Get conversation history from channel
        conversation_history = self._get_conversation_history(channel, odoobot)

        # Use LLM to generate response (use cleaned body without @mention)
        try:
            llm_client = self.env['wfm.llm.client']
            response = llm_client.chat_with_tools(clean_body, conversation_history)

            if response:
                # Format response for HTML display
                # Convert markdown-like formatting to HTML
                formatted = self._format_llm_response(response)
                return formatted

        except Exception as e:
            _logger.error(f"LLM chat error: {e}", exc_info=True)
            return self._get_error_response()

        return super()._get_answer(channel, body, values, command)

    def _get_conversation_history(self, channel, odoobot):
        """
        Retrieve recent conversation history from the mail channel.

        Returns list of messages in OpenAI format:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        history = []

        try:
            # Get recent messages from the channel (excluding the current one)
            messages = self.env['mail.message'].search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', channel.id),
                ('message_type', 'in', ['comment', 'notification']),
            ], order='id desc', limit=MAX_HISTORY_MESSAGES + 1)

            # Skip the first message (current user message) and reverse to chronological order
            messages = list(reversed(messages[1:] if len(messages) > 1 else []))

            for msg in messages:
                # Determine role based on author
                if msg.author_id == odoobot:
                    role = "assistant"
                else:
                    role = "user"

                # Clean HTML from message body
                content = self._strip_html(msg.body or "")
                if content.strip():
                    history.append({
                        "role": role,
                        "content": content.strip()
                    })

        except Exception as e:
            _logger.warning(f"Failed to get conversation history: {e}")

        return history

    def _strip_html(self, html_content):
        """Remove HTML tags and decode entities from message content."""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        # Decode HTML entities
        text = html.unescape(text)
        return text

    def _is_odoobot_mentioned(self, body, odoobot):
        """Check if OdooBot is mentioned in the message body."""
        import re
        # Check for @OdooBot text mention
        if '@odoobot' in body.lower():
            return True
        # Check for HTML mention format (Odoo uses data-oe-id attribute)
        if f'data-oe-id="{odoobot.id}"' in body:
            return True
        # Check for partner mention format
        if f'@data-oe-model="res.partner"' in body and str(odoobot.id) in body:
            return True
        # Check for simple name mention
        if 'odoobot' in body.lower():
            return True
        return False

    def _clean_mention(self, body, odoobot):
        """Remove @OdooBot mention from message body for cleaner LLM processing."""
        import re
        # Remove HTML mention tags
        clean = re.sub(r'<a[^>]*data-oe-id="' + str(odoobot.id) + r'"[^>]*>@?[^<]*</a>', '', body)
        # Remove plain @OdooBot text
        clean = re.sub(r'@odoobot\s*', '', clean, flags=re.IGNORECASE)
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean if clean else body

    def _format_llm_response(self, response):
        """Format LLM response for display in Odoo chat."""
        if not response:
            return None

        # Basic markdown to HTML conversion for chat display
        lines = response.split('\n')
        formatted_lines = []

        for line in lines:
            # Convert bullet points
            if line.strip().startswith('- '):
                line = Markup('&bull; ') + line.strip()[2:]
            elif line.strip().startswith('* '):
                line = Markup('&bull; ') + line.strip()[2:]

            # Convert bold **text** to <b>text</b>
            while '**' in line:
                line = line.replace('**', '<b>', 1)
                if '**' in line:
                    line = line.replace('**', '</b>', 1)
                else:
                    line = line + '</b>'

            formatted_lines.append(line)

        result = Markup('<br>').join(formatted_lines)
        return result

    def _get_error_response(self):
        """Return a friendly error message."""
        return Markup(
            "Sorry, I'm having trouble processing your request right now. "
            "Please try again in a moment or contact support if the issue persists."
        )


class ResUsers(models.Model):
    """Extend res.users to track conversation state."""

    _inherit = 'res.users'

    # We could add conversation history tracking here if needed
    # For now, conversations are stateless (no memory between messages)
