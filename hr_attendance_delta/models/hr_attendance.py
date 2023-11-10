import logging

from datetime import datetime, date
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    delta_hours = fields.Float(
        compute="_compute_delta_hours", store=True, readonly=True
    )

    @api.depends("check_in")
    def _compute_delta_hours(self):
        """Get the last attendance entry on that day
        and calculate the timespan between."""
        for attendance in self:
            start_datetime = datetime.combine(attendance.check_in, datetime.min.time())
            last_attendance = self.env["hr.attendance"].search(
                [
                    ("employee_id", "=", attendance.employee_id.id),
                    ("check_in", ">=", start_datetime),
                    ("check_out", "<=", attendance.check_in),
                ],
                limit=1,
            )
            if last_attendance:                
                attendance.delta_hours = (attendance.check_in - last_attendance.check_out).total_seconds() / 3600
            else:
                attendance.delta_hours = 0.0

    @api.onchange("check_out")
    def _update_next_attendance(self):
        """Get the next attendance entry on that day
        and update the timespan between."""
        for attendance in self.filtered("check_out"):
            end_datetime = datetime.combine(attendance.check_out, datetime.max.time())
            next_attendance = self.env["hr.attendance"].search(
                [
                    ("employee_id", "=", attendance.employee_id.id),
                    ("check_out", "<=", end_datetime),
                    ("check_in", ">=", attendance.check_out),
                ],
                limit=1,
            )            
            if next_attendance:
                next_attendance.delta_hours = (next_attendance.check_in - attendance.check_out).total_seconds() / 3600