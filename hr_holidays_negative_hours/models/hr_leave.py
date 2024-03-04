import logging

from odoo import api, models, fields
_logger = logging.getLogger(__name__)

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    allow_negative_hours = fields.Boolean(string="Allow Negative Hours", default=True)
    leave_validation_type = fields.Selection(default='no_validation')

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def _check_overtime_deductible(self, leaves):
        for leave in leaves:
            if leave.holiday_status_id.allow_negative_hours or leave.holiday_status_id.leave_validation_type == 'no_validation':
                continue
            employee = leave.employee_id.id
            duration = leave.number_of_hours_display
            if duration > employee.total_overtime:
                return True
            if not leave.overtime_id:
                return True
