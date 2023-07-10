import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit='project.project'

    limit_timehseet_amount = fields.Boolean(help='Limit timesheet amount to planned hours.')


class ProjectTask(models.Model):
    _inherit='project.task'

    @api.onchange('planned_hours')
    def _check_limit_timehseet_amount(self):
        """Effective hours must no exceed planned hours."""
        for task in self.filtered(lambda t: t.planned_hours != 0.0 and t.project_id.limit_timehseet_amount):

            effective_hours = task.effective_hours + task.subtask_effective_hours # - line.unit_amount
            planned_hours = task.planned_hours # + task.subtask_planned_hours
            # _logger.warning([effective_hours, planned_hours])

            if effective_hours > planned_hours:
                raise UserError(_('The timesheeted amount exceeds the planned hours (%(planned_hours)s) of this task.') % {
                    'planned_hours': planned_hours
                })
