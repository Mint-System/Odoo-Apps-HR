import logging

from odoo.exceptions import UserError

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = "project.project"

    limit_timehseet_amount = fields.Boolean(
        help="Limit timesheet amount to planned hours."
    )


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.onchange("allocated_hours")
    def _check_limit_timehseet_amount(self, unit_amount=0, line=None):
        """Effective hours must no exceed allocated hours."""

        # small tolerance becaus of rounding issues
        TOLERANCE = 0.01

        for task in self.filtered(
            lambda t: t.allocated_hours != 0.0 and t.project_id.limit_timehseet_amount
        ):
            effective_hours = task.effective_hours
            allocated_hours = task.allocated_hours

            # Workaround to get the real amount effective hours
            if (effective_hours - unit_amount) > task._origin.effective_hours:
                effective_hours = task._origin.effective_hours

            # If new amount is greater than existing hours, add the amount
            if (
                line
                and (unit_amount >= line._origin.unit_amount)
                or not line
                and unit_amount > 0.0
            ):
                effective_hours += unit_amount

            # If task is not a sub task, add the subtask effective hours
            if not task.parent_id:
                effective_hours += task.subtask_effective_hours

            # _logger.warning([effective_hours, planned_hours, task.subtask_planned_hours])

            if effective_hours > (allocated_hours + TOLERANCE):
                raise UserError(
                    _(
                        "The timesheeted amount exceeds the allocated hours (%(allocated_hours)s) of the task."
                    )
                    % {
                        "allocated_hours": allocated_hours
                        - task.subtask_allocated_hours
                        + (task.subtask_allocated_hours - task.subtask_effective_hours)
                    }
                )
