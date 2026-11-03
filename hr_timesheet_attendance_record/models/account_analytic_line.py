from datetime import timedelta

from odoo import api, fields, models, exceptions
from odoo.tools.float_utils import float_is_zero

class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    attendance_id = fields.Many2one("hr.attendance", string="Attendance", ondelete="restrict")

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
            attendance = self._get_attendance_record(date, employee_id)
            if attendance:
                record.attendance_id = attendance
            else:
                record.attendance_id = self._create_attendance(date, employee_id)
            record.attendance_id._update_overtime()
        return records

    def write(self, vals):
        current_attendance = self.attendance_id
        res = super().write(vals)
        if "unit_amount" in vals:
            current_attendance._update_overtime()
        if "date" in vals or "employee_id" in vals:
            had_only_self = len(current_attendance.timesheet_ids) == 1
            super(AccountAnalyticLine, self).write({'attendance_id': False})
            if had_only_self:
                current_attendance.unlink()
            else:
                current_attendance._update_overtime()
            new_attendance_id = self._get_attendance_record(self.date, self.employee_id.id)
            if not new_attendance_id:
                new_attendance_id = self._create_attendance(self.date, self.employee_id.id)
            super(AccountAnalyticLine, self).write({'attendance_id': new_attendance_id})
            self.attendance_id._update_overtime()
        return res

    def unlink(self):
        for rec in self:
            attendance = rec.attendance_id
            super(AccountAnalyticLine, rec).unlink()
            if len(attendance.timesheet_ids) == 0:
                attendance.unlink()
            else:
                attendance._update_overtime()
        return True