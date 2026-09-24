from datetime import timedelta

from odoo import api, fields, models, exceptions
from odoo.tools.float_utils import float_is_zero

class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    attendance_id = fields.Many2one("hr.attendance", string="Attendance")

    def _get_attendance_record(self, date, employee_id):
        date = fields.Date.to_date(date)
        start = fields.Datetime.to_datetime(date)
        end = start + timedelta(days=1)
        attendances = self.env["hr.attendance"].search([
            ("employee_id", "=", employee_id),
            ("check_in", ">=", start),
            ("check_in", "<", end),
        ])
        if len(attendances) > 1:
            raise exceptions.ValidationError("Multiple attendances found for the given date and employee.")
        return attendances.id if attendances else False

    def _create_attendance(self, date, employee_id):
        check_in = fields.Datetime.to_datetime(date) + timedelta(hours=8)
        attendance = self.env["hr.attendance"].create({
            "employee_id": employee_id,
            "check_in": check_in,
        })
        return attendance.id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            date = record.date
            employee_id = record.employee_id.id
            if date and employee_id:
                attendance = self._get_attendance_record(date, employee_id)
                if attendance:
                    record.attendance_id = attendance
                else:
                    record.attendance_id = self._create_attendance(date, employee_id)
        return records

    def unlink(self):
        attendances = self.mapped('attendance_id')
        result = super().unlink()
        attendances_to_unlink = attendances.filtered(
            lambda a: len(a.timesheet_ids) == 0
        )
        if attendances_to_unlink:
            attendances_to_unlink.unlink()
        return result