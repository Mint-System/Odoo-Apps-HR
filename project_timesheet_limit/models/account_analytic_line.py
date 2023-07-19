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
            line.task_id._check_limit_timehseet_amount(line.unit_amount, line)

    @api.model_create_multi
    def create(self, vals_list):
        """Check if timesheeted amount surpasses the tasks planned hours."""
        for vals in vals_list:
            task_id = self.env['project.task'].browse(vals.get('task_id'))
            if task_id:
                task_id._check_limit_timehseet_amount(vals.get('unit_amount'))
        return super(AccountAnalyticLine, self).create(vals_list)