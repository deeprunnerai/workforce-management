from odoo import models, fields


class WfmVisitStage(models.Model):
    _name = 'wfm.visit.stage'
    _description = 'Visit Stage'
    _order = 'sequence, id'

    name = fields.Char(
        string='Stage Name',
        required=True,
        translate=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Used to order stages. Lower is better.'
    )
    fold = fields.Boolean(
        string='Folded in Kanban',
        default=False,
        help='This stage is folded in the kanban view when there are no records in that stage.'
    )
    description = fields.Text(
        string='Description',
        translate=True
    )

    # For dashboard color coding
    is_completed = fields.Boolean(
        string='Is Completed Stage',
        default=False,
        help='Visits in this stage are considered completed'
    )
