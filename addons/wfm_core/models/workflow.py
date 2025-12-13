import logging
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WfmWorkflow(models.Model):
    """Autonomous Agent Workflow - defines automated tasks executed by LLM."""

    _name = 'wfm.workflow'
    _description = 'WFM Autonomous Workflow'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )
    description = fields.Text(
        string='Description',
        help='Human-readable description of what this workflow does'
    )
    prompt = fields.Text(
        string='Agent Prompt',
        required=True,
        help='Natural language instruction for the LLM agent'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )

    # Schedule Configuration
    schedule_type = fields.Selection([
        ('manual', 'Manual Only'),
        ('interval', 'Interval'),
        ('cron', 'Cron Expression'),
    ], string='Schedule Type', default='manual', required=True)

    interval_number = fields.Integer(
        string='Interval Number',
        default=1,
        help='Number of intervals between executions'
    )
    interval_type = fields.Selection([
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
    ], string='Interval Type', default='hours')

    cron_expression = fields.Char(
        string='Cron Expression',
        help='Cron expression (e.g., "0 9 * * *" for daily at 9AM)'
    )
    cron_description = fields.Char(
        string='Schedule Description',
        compute='_compute_cron_description'
    )

    # Execution Settings
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    max_tool_calls = fields.Integer(
        string='Max Tool Calls',
        default=50,
        help='Maximum number of tool calls per execution (safety limit)'
    )
    timeout_minutes = fields.Integer(
        string='Timeout (minutes)',
        default=5,
        help='Maximum execution time before timeout'
    )

    # Execution Tracking
    last_run = fields.Datetime(
        string='Last Run',
        readonly=True
    )
    next_run = fields.Datetime(
        string='Next Run',
        compute='_compute_next_run',
        store=True
    )
    run_count = fields.Integer(
        string='Total Runs',
        default=0,
        readonly=True
    )
    success_count = fields.Integer(
        string='Successful Runs',
        default=0,
        readonly=True
    )
    fail_count = fields.Integer(
        string='Failed Runs',
        default=0,
        readonly=True
    )
    success_rate = fields.Float(
        string='Success Rate (%)',
        compute='_compute_success_rate'
    )

    # Relations
    created_by_id = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True
    )
    log_ids = fields.One2many(
        'wfm.workflow.log',
        'workflow_id',
        string='Execution Logs'
    )
    log_count = fields.Integer(
        string='Log Count',
        compute='_compute_log_count'
    )

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('error', 'Error'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('log_ids')
    def _compute_log_count(self):
        for workflow in self:
            workflow.log_count = len(workflow.log_ids)

    @api.depends('run_count', 'success_count')
    def _compute_success_rate(self):
        for workflow in self:
            if workflow.run_count > 0:
                workflow.success_rate = (workflow.success_count / workflow.run_count) * 100
            else:
                workflow.success_rate = 0.0

    @api.depends('schedule_type', 'cron_expression', 'interval_number', 'interval_type')
    def _compute_cron_description(self):
        for workflow in self:
            if workflow.schedule_type == 'manual':
                workflow.cron_description = 'Manual trigger only'
            elif workflow.schedule_type == 'interval':
                workflow.cron_description = f'Every {workflow.interval_number} {workflow.interval_type}'
            elif workflow.schedule_type == 'cron' and workflow.cron_expression:
                workflow.cron_description = self._parse_cron_to_text(workflow.cron_expression)
            else:
                workflow.cron_description = 'Not configured'

    @api.depends('schedule_type', 'last_run', 'interval_number', 'interval_type', 'cron_expression', 'active')
    def _compute_next_run(self):
        for workflow in self:
            if not workflow.active or workflow.schedule_type == 'manual':
                workflow.next_run = False
                continue

            base_time = workflow.last_run or fields.Datetime.now()

            if workflow.schedule_type == 'interval':
                delta_map = {
                    'minutes': timedelta(minutes=workflow.interval_number),
                    'hours': timedelta(hours=workflow.interval_number),
                    'days': timedelta(days=workflow.interval_number),
                    'weeks': timedelta(weeks=workflow.interval_number),
                }
                delta = delta_map.get(workflow.interval_type, timedelta(hours=1))
                workflow.next_run = base_time + delta

            elif workflow.schedule_type == 'cron' and workflow.cron_expression:
                workflow.next_run = self._get_next_cron_time(workflow.cron_expression)
            else:
                workflow.next_run = False

    def _parse_cron_to_text(self, cron_expr):
        """Convert cron expression to human-readable text."""
        if not cron_expr:
            return 'Invalid'

        parts = cron_expr.split()
        if len(parts) != 5:
            return cron_expr

        minute, hour, day, month, weekday = parts

        # Common patterns
        if cron_expr == '* * * * *':
            return 'Every minute'
        if minute == '0' and hour == '*':
            return 'Every hour'
        if minute == '0' and hour.isdigit():
            h = int(hour)
            period = 'AM' if h < 12 else 'PM'
            h_12 = h if h <= 12 else h - 12
            if h_12 == 0:
                h_12 = 12
            if weekday == '*' and day == '*':
                return f'Daily at {h_12}:00 {period}'
            if weekday.isdigit():
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                day_name = days[int(weekday) % 7]
                return f'Every {day_name} at {h_12}:00 {period}'

        return cron_expr

    def _get_next_cron_time(self, cron_expr):
        """Calculate next execution time from cron expression."""
        try:
            from croniter import croniter
            cron = croniter(cron_expr, datetime.now())
            return cron.get_next(datetime)
        except ImportError:
            # Fallback: just add 1 hour if croniter not available
            return fields.Datetime.now() + timedelta(hours=1)
        except Exception:
            return False

    def action_activate(self):
        """Activate the workflow."""
        for workflow in self:
            workflow.write({
                'state': 'active',
                'active': True,
            })

    def action_pause(self):
        """Pause the workflow."""
        for workflow in self:
            workflow.write({
                'state': 'paused',
                'active': False,
            })

    def action_run_now(self):
        """Manually trigger workflow execution."""
        self.ensure_one()
        return self._execute()

    def _execute(self):
        """Execute the workflow using LLM."""
        self.ensure_one()

        log = self.env['wfm.workflow.log'].create({
            'workflow_id': self.id,
            'started_at': fields.Datetime.now(),
            'status': 'running',
            'prompt_used': self.prompt,
        })

        try:
            # Get LLM client and execute
            llm_client = self.env['wfm.llm.client']

            # Build context-aware prompt
            system_context = f"""You are executing an autonomous workflow.
Workflow: {self.name}
Current time: {fields.Datetime.now()}

Execute the following task completely. Use the available tools to accomplish the goal.
If you encounter errors, log them and continue with what you can do.
"""
            full_prompt = f"{system_context}\n\nTask:\n{self.prompt}"

            # Execute with tools
            result = llm_client.chat_with_tools(full_prompt)

            # Update log with success
            log.write({
                'ended_at': fields.Datetime.now(),
                'status': 'success',
                'result': result,
            })

            # Update workflow stats
            self.write({
                'last_run': fields.Datetime.now(),
                'run_count': self.run_count + 1,
                'success_count': self.success_count + 1,
                'state': 'active',
            })

            return result

        except Exception as e:
            _logger.error(f"Workflow {self.name} failed: {e}")

            log.write({
                'ended_at': fields.Datetime.now(),
                'status': 'failed',
                'error': str(e),
            })

            self.write({
                'last_run': fields.Datetime.now(),
                'run_count': self.run_count + 1,
                'fail_count': self.fail_count + 1,
                'state': 'error',
            })

            return False

    def action_view_logs(self):
        """Open logs for this workflow."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Execution Logs'),
            'res_model': 'wfm.workflow.log',
            'view_mode': 'list,form',
            'domain': [('workflow_id', '=', self.id)],
            'context': {'default_workflow_id': self.id},
        }

    @api.model
    def run_scheduled_workflows(self):
        """Cron job: Execute all workflows that are due."""
        now = fields.Datetime.now()

        # Find active workflows that are due
        due_workflows = self.search([
            ('active', '=', True),
            ('state', '=', 'active'),
            ('schedule_type', '!=', 'manual'),
            '|',
            ('next_run', '<=', now),
            ('next_run', '=', False),
        ])

        _logger.info(f"Running {len(due_workflows)} scheduled workflows")

        for workflow in due_workflows:
            try:
                workflow._execute()
            except Exception as e:
                _logger.error(f"Failed to execute workflow {workflow.name}: {e}")

        return True
