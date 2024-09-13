import logging
from datetime import datetime

import pytz

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = "hr.leave"

    attendance_ids = fields.One2many("hr.attendance", "leave_id")
    attendance_count = fields.Integer(compute="_compute_attendance_count")
    record_as_attendance = fields.Boolean(compute="_compute_record_as_attendance")
    work_hours = fields.Integer("_compute_work_hours")

    @api.depends("attendance_ids")
    def _compute_attendance_count(self):
        for leave in self:
            leave.attendance_count = len(leave.attendance_ids)

    def action_attendance_view(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.attendance",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.attendance_ids.ids)],
        }

    def _compute_record_as_attendance(self):
        for leave in self:
            leave.record_as_attendance = (
                leave.holiday_status_id.record_as_attendance
                and (
                    leave.holiday_status_id.max_leave_hours == 0
                    or leave.number_of_hours_display
                    <= leave.holiday_status_id.max_leave_hours
                )
            )

    @api.depends("request_date_from", "request_date_to")
    def _compute_work_hours():
        for leave in self:
            if leave.record_as_attendance:

                # Get calendar
                calendar_id = (
                    leave.holiday_status_id.calendar_id
                    or leave.employee_id.resource_calendar_id
                )
                leave.attendance_hours = calendar_id.get_work_hours_count(
                    leave.request_date_from, leave.request_date_to
                )
            else:
                leave.attendance_hours = 0

    def action_confirm(self):
        """
        Create attendance entries if leave is recorded as attendance.
        """
        res = super().action_confirm()

        if self.record_as_attendance:

            # Get calendar
            calendar_id = (
                self.holiday_status_id.calendar_id
                or self.employee_id.resource_calendar_id
            )
            pytz.timezone(calendar_id.tz)

            # Create attendance based on unit type
            if not self.request_unit_half and not self.request_unit_hours:

                # Create an attendance for each day.
                self.request_date_from

                # The checkin time is defined by the calendar

                # The checkout time is checkin plus average hours from calendar

            elif self.leave_type_request_unit == "half_day":

                # Get worked hours for leave days
                worked_hours = sum(
                    self.env["hr.attendance"]
                    .search_read(
                        [
                            ("employee_id", "=", self.employee_id.id),
                            ("check_in", ">=", self.request_date_from),
                            ("check_out", "<=", self.request_date_to),
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
                        "check_in": self.request_date_from,
                        "check_out": self.request_date_to,
                        "leave_id": self.id,
                    }
                )
            elif self.leave_type_request_unit == "hour":

                # Create an attendance for the selected hours
                check_in = datetime.combine(
                    self.request_date_from, self.request_hour_from
                )
                check_out = datetime.combine(self.request_date_to, self.request_hour_to)
                self.env["hr.attendance"].create(
                    {
                        "employee_id": self.employee_id.id,
                        "check_in": check_in,
                        "check_out": check_out,
                        "leave_id": self.id,
                    }
                )

        return res

        def action_draft(self):
            res = super().action_draft()
            self.sudo().leave_ids.unlink()
            return res

        def unlink(self):
            self.sudo().leave_ids.unlink()
            return super().unlink()
