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

    # def _check_overtime_deductible(self, leaves):
    #     for leave in leaves:
    #         if not leave.overtime_deductible:
    #             continue
    #         employee = leave.employee_id.sudo()
    #         duration = leave.number_of_hours_display
    #         if duration <= employee.total_overtime:
    #             if not leave.overtime_id:
    #                 leave.sudo().overtime_id = self.env['hr.attendance.overtime'].sudo().create({
    #                     'employee_id': employee.id,
    #                     'date': leave.date_from,
    #                     'adjustment': True,
    #                     'duration': -1 * duration,
    #                 })

    # def _check_overtime_deductible(self):
    #     try:
    #         super()._check_overtime_deductible()
    #     except:
    #         return True


    # def _check_overtime_deductible(self):
    #     for leave in self:
    #         if leave.holiday_status_id.allow_negative_hours and leave.employee_id.employee_overtime < 0:
    #             continue
    #         try:
    #             super(self)._check_overtime_deductible()
    #         except ValidationError:
    #             return True

    # def _check_overtime_deductible(self, leaves):
    #     for leave in leaves:
    #         if leave.holiday_status_id.allow_negative_hours:
    #             # Bypass the overtime deduction check if negative hours are allowed
    #             continue
    #         if not leave.overtime_deductible:
    #             continue
    #         employee = leave.employee_id.sudo()
    #         duration = leave.number_of_hours_display
    #         if duration > employee.total_overtime:
    #             # Only raise the ValidationError if allow_negative_hours is False
    #             raise ValidationError(_('The employee does not have enough extra hours to request this leave.'))
    #         if not leave.overtime_id:
    #             leave.sudo().overtime_id = self.env['hr.attendance.overtime'].sudo().create({
    #                 'employee_id': employee.id,
    #                 'date': leave.date_from,
    #                 'adjustment': True,
    #                 'duration': -1 * duration,
    #             })
