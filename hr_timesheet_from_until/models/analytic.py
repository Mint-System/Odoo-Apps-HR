from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    from_time = fields.Float(default=0.0, group_operator=None)
    until_time = fields.Float(default=0.0, group_operator=None)
    unit_amount = fields.Float(compute='_compute_unit_amount', readonly=False, store=True)

    def _convert(self, time):
        """Converts time from integer to float."""
        time_str = "{:.2f}".format(time/100)
        time_hour = int(time_str.split(".")[0])
        time_min = float(time_str.split(".")[1])/60
        return time_hour + time_min

    @api.depends('from_time', 'until_time')
    def _compute_unit_amount(self):
        """Compute amount from time delta."""
        for rec in self:
            from_time = rec.from_time
            until_time = rec.until_time
            if from_time > 100:
                from_time = self._convert(from_time)
                rec.from_time = from_time
            if until_time > 100:
                until_time = self._convert(until_time)
                rec.until_time = until_time
            if from_time < until_time < 24:
                rec.unit_amount =  until_time - from_time
            else:
                rec.unit_amount = 0
    
