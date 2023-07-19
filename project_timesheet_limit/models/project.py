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
    def _check_limit_timehseet_amount(self, unit_amount, line=None):
        """Effective hours must no exceed planned hours."""
        for task in self.filtered(lambda t: t.planned_hours != 0.0 and t.project_id.limit_timehseet_amount):

            effective_hours = task.effective_hours # - line.unit_amount
            planned_hours = task.planned_hours # + task.subtask_planned_hours

            _logger.warning([effective_hours, planned_hours])

            # If new amount is greater than existing hours, add the amount
            if line and (unit_amount > line._origin.unit_amount) or not line and unit_amount > 0.0:
                effective_hours += unit_amount

            # If task is not a sub task, add the subtask effective hours
            if not task.parent_id:
                effective_hours += task.subtask_effective_hours
            
            _logger.warning([effective_hours, planned_hours])
            
            if effective_hours > planned_hours:
                raise UserError(_('The timesheeted amount exceeds the planned hours (%(planned_hours)s) of the task.') % {
                    'planned_hours': planned_hours
                })
