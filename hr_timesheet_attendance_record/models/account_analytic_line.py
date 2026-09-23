from datetime import timedelta

from odoo import api, fields, models, exceptions


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
        vals_list = [vals.copy() for vals in vals_list]
        for vals in vals_list:
            date = vals.get("date")
            employee_id = vals.get("employee_id")
            if date and employee_id:
                attendance = self._get_attendance_record(date, employee_id)
                if attendance:
                    vals["attendance_id"] = attendance
                else:
                    vals["attendance_id"] = self._create_attendance(date, employee_id)
        return super().create(vals_list)

    def unlink(self):
        attendances_to_unlink = self.env["hr.attendance"]
        for record in self:
            if record.attendance_id and len(record.attendance_id.timesheet_ids) == 1:
                attendances_to_unlink |= record.attendance_id
        result = super().unlink()
        attendances_to_unlink.unlink()
        return result
