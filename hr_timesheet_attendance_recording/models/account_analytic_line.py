# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import pytz

from datetime import datetime, time, timedelta
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    attendance_id = fields.Many2one(
        "hr.attendance",
        string="Attendance",
        ondelete="set null",
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if not record.employee_id:
                continue

            date = record.date
            employee = record.employee_id

            # Get employee timezone, fallback on user / company / UTC
            tz_name = (
                employee.tz
                or self.env.user.tz
                or self.env.company.partner_id.tz
                or "UTC"
            )
            tz = pytz.timezone(tz_name)

            # Search attendances from the same employee on the same date
            local_start_naive = datetime.combine(date, time.min)
            local_end_naive = datetime.combine(date + timedelta(days=1), time.min)

            utc_start = (
                tz.localize(local_start_naive)
                .astimezone(pytz.utc)
                .replace(tzinfo=None)
            )
            utc_end = (
                tz.localize(local_end_naive)
                .astimezone(pytz.utc)
                .replace(tzinfo=None)
            )

            attendances = self.env["hr.attendance"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("check_in", ">=", utc_start),
                    ("check_in", "<", utc_end),
                ]
            )

            # Look for an existing attendance, unlink all others on the same day.
            existing_attendance = False
            for attendance in attendances:
                if attendance.timesheet_ids:
                    existing_attendance = attendance
                elif not attendance.timesheet_ids or existing_attendance:
                    attendance.unlink()

            if not existing_attendance:
                check_in = (
                    tz.localize(datetime.combine(date, time(8, 0)))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                )
                existing_attendance = self.env["hr.attendance"].create(
                    {
                        "employee_id": employee.id,
                        "check_in": check_in,
                        "timesheet_ids": [(4, record.id)],
                    }
                )
            else:
                existing_attendance.write(
                    {
                        "timesheet_ids": [(4, record.id)],
                    }
                )
                record.attendance_id._compute_check_out()

            record.attendance_id = existing_attendance.id

        return records

    def unlink(self):
        for record in self:
            if record.attendance_id:
                attendance = record.attendance_id
                if len(attendance.timesheet_ids) == 1:
                    attendance.unlink()
                else:
                    attendance.write(
                        {
                            "timesheet_ids": [(3, record.id)],
                        }
                    )
                    record.attendance_id._compute_check_out()
        return super().unlink()

    def write(self, vals):
        result = super().write(vals)
        if "unit_amount" in vals:
            for record in self:
                if record.attendance_id:
                    record.attendance_id._compute_check_out()
        return result
