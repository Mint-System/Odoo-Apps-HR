import logging
from datetime import datetime, timedelta

import pytz

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = "hr.leave"

    attendance_ids = fields.One2many("hr.attendance", "leave_id")
    attendance_count = fields.Integer(compute="_compute_attendance_count")
    record_as_attendance = fields.Boolean(compute="_compute_record_as_attendance")
    work_hours = fields.Float("_compute_work_hours", store=True)

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
            if leave.attendance_ids:
                leave.record_as_attendance = False
            leave.record_as_attendance = (
                leave.holiday_status_id.record_as_attendance
                and (
                    leave.holiday_status_id.max_leave_hours == 0
                    or leave.number_of_hours_display
                    <= leave.holiday_status_id.max_leave_hours
                )
            )

    def get_calendar_id(self):
        self.ensure_one()
        return (
            self.holiday_status_id.calendar_id or self.employee_id.resource_calendar_id
        )

    @api.depends("request_date_from", "request_date_to")
    def _compute_work_hours():
        for leave in self:
            if leave.record_as_attendance:

                # Get calendar
                calendar_id = leave.get_calendar_id()

                date_from = datetime.combine(
                    leave.request_date_from, datetime.min.time()
                )
                date_to = datetime.combine(leave.request_date_to, datetime.max.time())

                leave.attendance_hours = calendar_id.get_work_hours_count(
                    date_from, date_to
                )
            else:
                leave.attendance_hours = 0

    def get_work_hour(self, date, day_period):
        self.ensure_one()
        dayofweek = date.weekday()
        work_hour_id = self.env["resource.calendar.attendance"].search(
            [
                ("calendar_id", "=", self.get_calendar_id().id),
                ("dayofweek", "=", dayofweek),
                ("day_period", "=", day_period),
            ],
            limit=1,
        )
        return work_hour_id.hour_from

    def action_confirm(self):
        res = super().action_confirm()
        self.create_attendances()
        return res

    def action_approve(self):
        res = super().action_approve()
        self.create_attendances()
        return res

    def create_attendances(self):
        self.ensure_one()
        """
        Create attendance entries if leave is recorded as attendance.
        """

        if self.record_as_attendance:

            # Get calendar and timezone
            calendar_id = self.get_calendar_id()
            user_tz = pytz.timezone(self.tz)

            _logger.warning(
                [
                    self.request_date_from,
                    self.request_date_to,
                    self.request_hour_from,
                    self.request_hour_to,
                    user_tz,
                ]
            )

            # Create attendance based on unit type
            if not self.request_unit_half and not self.request_unit_hours:

                # Convert to datetime
                start_date = datetime.combine(
                    self.request_date_from, datetime.min.time()
                )
                end_date = datetime.combine(self.request_date_to, datetime.max.time())

                # Create an attendance for each day.
                attendance_vals = []
                while start_date <= end_date:

                    work_hours = calendar_id.get_work_hours_count(
                        start_date, start_date + timedelta(days=1)
                    )
                    if work_hours > 0:

                        # Get start and end time in hours
                        hour_from = self.get_work_hour(start_date, "morning")
                        hour_to = hour_from + work_hours

                        # Convert from user tz to utc
                        date_from = (
                            user_tz.localize(start_date)
                            .astimezone(pytz.utc)
                            .replace(tzinfo=None)
                        )

                        # The checkin time is defined by the calendar
                        # The checkout time is checkin plus average hours from calendar
                        attendance_vals.append(
                            {
                                "employee_id": self.employee_id.id,
                                "check_in": date_from + timedelta(hours=hour_from),
                                "check_out": date_from + timedelta(hours=hour_to),
                                "leave_id": self.id,
                            }
                        )

                    start_date += timedelta(days=1)

                self.env["hr.attendance"].sudo().create(attendance_vals)

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

                self.env["hr.attendance"].sudo().create(
                    {
                        "employee_id": self.employee_id.id,
                        "check_in": self.request_date_from,
                        "check_out": self.request_date_to,
                        "leave_id": self.id,
                    }
                )

            elif self.leave_type_request_unit == "hour":

                # Convert to datetime
                check_in = datetime.combine(self.request_date_from, datetime.min.time())

                # Convert from user tz to utc
                check_in = (
                    user_tz.localize(check_in).astimezone(pytz.utc).replace(tzinfo=None)
                )

                # Add hours to datetime
                check_out = check_in + timedelta(hours=self.request_time_hour_to)
                check_in = check_in + timedelta(hours=self.request_time_hour_from)

                self.env["hr.attendance"].sudo().create(
                    {
                        "employee_id": self.employee_id.id,
                        "check_in": check_in,
                        "check_out": check_out,
                        "leave_id": self.id,
                    }
                )

    def action_draft(self):
        res = super().action_draft()
        self.sudo().attendance_ids.unlink()
        return res

    def unlink(self):
        self.sudo().attendance_ids.unlink()
        return super().unlink()

    def action_cancel_leave(self):
        res = super().action_cancel_leave()
        self.sudo().attendance_ids.unlink()
        return res