from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)




class HrAttendanceOvertime(models.Model):
    _inherit = 'hr.attendance.overtime'

    paid_out = fields.Boolean(store=True, readonly=True, default=False)
    date = fields.Date(string='Day')
    duration = fields.Float(string='Extra Hours', default=0.0, required=True)

    @api.constrains('date', 'paid_out')
    def _check_date_required_if_paid_out(self):
        for record in self:
            if record.paid_out and not record.date:
                raise ValidationError("Date is required for paid out overtimes.")

    @api.constrains('duration', 'paid_out')
    def _check_duration(self):
        for record in self:
            if record.paid_out and record.duration >= 0:
                raise ValidationError("Duration must be negative.")

