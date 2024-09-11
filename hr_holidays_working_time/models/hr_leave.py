import logging
from datetime import datetime

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = "hr.leave"

    leave_ids = fields.One2many("hr.attendance", "leave_id")
    leave_count = fields.Integer(compute="_compute_leave_count")
    record_as_attendance = fields.Boolean(compute="_compute_record_as_attendance")
    work_hours = fields.Integer("_compute_work_hours")

    @api.depends("leave_ids")
    def _compute_leave_count(self):
        for leave in self:
            leave.leave_count = len(leave.leave_ids)

    def _compute_record_as_attendance():
        for leave in self:
            leave.record_as_attendance = (
                leave.holiday_status_id.record_as_attendance
                and (
                    leave.holiday_status_id.max_leave_hours == 0
                    or leave.number_of_hours_display
                    <= leave.holiday_status_id.max_leave_hours
                )
            )

    @api.depends("from_date", "to_date")
    def _compute_work_hours():
        for leave in self:
            if leave.record_as_attendance:

                # Get calendar
                calendar_id = (
                    leave.holiday_status_id.calendar_id or leave.employee_id.calendar_id
                )
                leave.attendance_hours = calendar_id.get_work_hours_count(
                    leave.from_date, leave.to_date
                )
            else:
                leave.attendance_hours = 0

    def action_confirm(self):
        """
        Create attendance entries if leave is recorded as attendance.
        """
        super().action_confirm()

        if self.record_as_attendance:

            # Get calendar
            calendar_id = (
                self.holiday_status_id.calendar_id or self.employee_id.calendar_id
            )

            # Create attendance based on unit type
            if self.leave_type_request_unit == "day":

                # Create an attendance for each day.
                intervals_batch = calendar_id._attendance_intervals_batch(
                    self.from_date, self.to_date
                )
                for internval in intervals_batch:
                    _logger.warning(internval)

                    # The checkin time is defined by the calendar

                    # The checkout time is checkin plus average hours from calendar

            elif self.leave_type_request_unit == "half_day":

                # Get worked hours for leave days
                worked_hours = sum(
                    self.env["hr.attendance"]
                    .search_read(
                        [
                            ("employee_id", "=", self.employee_id.id),
                            ("check_in", ">=", self.from_date),
                            ("check_out", "<=", self.to_date),
                        ],
                        ["worked_hours"],
                    )
                    .mapped("worked_hours")
                )
                _logger.warning(worked_hours)

                # If request is morning use checkin time from calendar
                # and checkout time is plus working time minus worked time

                # If request is afternoon use checkout time from calendar
                # and checkin time is minus working time plus worked time

                self.env["hr.attendance"].create(
                    {
                        "employee_id": self.employee_id.id,
                        "check_in": self.from_date,
                        "check_out": self.to_date,
                        "leave_id": self.id,
                    }
                )
            elif self.leave_type_request_unit == "hour":

                # Create an attendance for the selected hours
                check_in = dateitme.combine(self.from_date, self.request_hour_from)
                check_out = datetime.combine(self.to_date, self.request_hour_to)
                self.env["hr.attendance"].create(
                    {
                        "employee_id": self.employee_id.id,
                        "check_in": check_in,
                        "check_out": check_out,
                        "leave_id": self.id,
                    }
                )

        def action_draft(self):
            res = super().action_draft()
            self.sudo().leave_ids.unlink()
            return res

        def unlink(self):
            self.sudo().leave_ids.unlink()
            return super().unlink()
