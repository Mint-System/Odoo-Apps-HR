import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.onchange('task_id', 'unit_amount')
    def _check_limit_timehseet_amount(self):
        """Check if timesheeted amount surpasses the tasks planned hours."""
        for line in self.filtered(lambda l: l.task_id):
            line.task_id._check_limit_timehseet_amount()

            # effective_hours = line.task_id.effective_hours + line.task_id.subtask_effective_hours # - line.unit_amount
            # planned_hours = line.task_id.planned_hours + line.task_id.subtask_planned_hours

            # _logger.warning([ line.task_id.effective_hours, line.task_id.planned_hours])
            # _logger.warning([line.task_id.subtask_effective_hours, line.task_id.subtask_planned_hours])
            # _logger.warning([effective_hours, planned_hours])
            
            # if effective_hours > planned_hours:
            #     raise UserError(_('The timesheeted amount exceeds the planned hours (%(planned_hours)s) of this task.') % {
            #         'planned_hours': line.task_id.planned_hours
            #     })
