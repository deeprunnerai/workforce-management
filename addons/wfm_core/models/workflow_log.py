import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class WfmWorkflowLog(models.Model):
    """Execution log for autonomous workflows."""

    _name = 'wfm.workflow.log'
    _description = 'Workflow Execution Log'
    _order = 'started_at desc'
    _rec_name = 'display_name'

    workflow_id = fields.Many2one(
        'wfm.workflow',
        string='Workflow',
        required=True,
        ondelete='cascade',
        index=True
    )
    workflow_name = fields.Char(
        related='workflow_id.name',
        store=True
    )

    # Timing
    started_at = fields.Datetime(
        string='Started At',
        required=True,
        default=fields.Datetime.now
    )
    ended_at = fields.Datetime(
        string='Ended At'
    )
    duration_seconds = fields.Float(
        string='Duration (s)',
        compute='_compute_duration',
        store=True
    )

    # Status
    status = fields.Selection([
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='running', required=True, index=True)

    # Execution Details
    prompt_used = fields.Text(
        string='Prompt Used',
        help='The actual prompt sent to the LLM'
    )
    tool_calls = fields.Text(
        string='Tool Calls (JSON)',
        help='JSON list of tools called during execution'
    )
    tool_call_count = fields.Integer(
        string='Tool Calls',
        compute='_compute_tool_call_count'
    )
    result = fields.Text(
        string='Result',
        help='Final response from the LLM'
    )
    error = fields.Text(
        string='Error',
        help='Error message if execution failed'
    )

    # Resource Usage
    tokens_input = fields.Integer(
        string='Input Tokens',
        default=0
    )
    tokens_output = fields.Integer(
        string='Output Tokens',
        default=0
    )
    tokens_total = fields.Integer(
        string='Total Tokens',
        compute='_compute_tokens_total'
    )

    # Computed
    display_name = fields.Char(
        compute='_compute_display_name'
    )

    @api.depends('started_at', 'ended_at')
    def _compute_duration(self):
        for log in self:
            if log.started_at and log.ended_at:
                delta = log.ended_at - log.started_at
                log.duration_seconds = delta.total_seconds()
            else:
                log.duration_seconds = 0

    @api.depends('tool_calls')
    def _compute_tool_call_count(self):
        import json
        for log in self:
            if log.tool_calls:
                try:
                    calls = json.loads(log.tool_calls)
                    log.tool_call_count = len(calls) if isinstance(calls, list) else 0
                except (json.JSONDecodeError, TypeError):
                    log.tool_call_count = 0
            else:
                log.tool_call_count = 0

    @api.depends('tokens_input', 'tokens_output')
    def _compute_tokens_total(self):
        for log in self:
            log.tokens_total = log.tokens_input + log.tokens_output

    @api.depends('workflow_id', 'started_at', 'status')
    def _compute_display_name(self):
        for log in self:
            if log.started_at:
                time_str = log.started_at.strftime('%Y-%m-%d %H:%M')
                log.display_name = f"{log.workflow_name} - {time_str} ({log.status})"
            else:
                log.display_name = f"{log.workflow_name} ({log.status})"

    def action_view_details(self):
        """Open form view with full details."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.display_name,
            'res_model': 'wfm.workflow.log',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def cleanup_old_logs(self, days=30):
        """Cron job: Delete logs older than specified days."""
        cutoff = fields.Datetime.now() - fields.Datetime.to_datetime(f'{days} days')
        old_logs = self.search([
            ('started_at', '<', cutoff),
            ('status', 'in', ['success', 'failed', 'timeout', 'cancelled']),
        ])
        count = len(old_logs)
        old_logs.unlink()
        _logger.info(f"Cleaned up {count} workflow logs older than {days} days")
        return count
