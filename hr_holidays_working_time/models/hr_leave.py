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
        """
        Create attendance entries if leave is recorded as attendance.
        """
        self.ensure_one()

        if self.record_as_attendance:

            # Get calendar and timezone
            calendar_id = self.get_calendar_id()
            user_tz = pytz.timezone(self.tz)

            # _logger.warning(
            #     [
            #         self.request_unit_half,
            #         self.request_unit_hours,
            #         self.request_date_from,
            #         self.request_date_to,
            #         self.request_hour_from,
            #         self.request_hour_to,
            #         user_tz,
            #     ]
            # )

            # Convert to datetime
            start_date = datetime.combine(self.request_date_from, datetime.min.time())
            end_date = datetime.combine(self.request_date_to, datetime.max.time())

            # Create attendance based on unit type
            attendance_vals = []

            if not self.request_unit_half and not self.request_unit_hours:

                # Create an attendance for each day.
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

            elif self.request_unit_half:

                attendance_vals = {
                    "employee_id": self.employee_id.id,
                    "leave_id": self.id,
                }

                # Get work hours
                work_hours = calendar_id.get_work_hours_count(start_date, end_date)

                # Convert from user tz to utc
                date_from = (
                    user_tz.localize(start_date)
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                )

                hour_from = 0
                if self.request_date_from_period == "am":
                    hour_from = self.get_work_hour(self.request_date_from, "morning")
                elif self.request_date_from_period == "pm":
                    hour_from = self.get_work_hour(self.request_date_from, "afternoon")

                hour_to = hour_from + work_hours / 2
                attendance_vals["check_in"] = date_from + timedelta(hours=hour_from)
                attendance_vals["check_out"] = date_from + timedelta(hours=hour_to)

            elif self.request_unit_hours:

                # Convert from user tz to utc
                check_in = (
                    user_tz.localize(start_date)
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                )

                # Add hours to datetime
                check_out = check_in + timedelta(hours=self.request_time_hour_to)
                check_in = check_in + timedelta(hours=self.request_time_hour_from)

                attendance_vals = {
                    "employee_id": self.employee_id.id,
                    "check_in": check_in,
                    "check_out": check_out,
                    "leave_id": self.id,
                }

            # _logger.warning(attendance_vals)
            self.env["hr.attendance"].sudo().create(attendance_vals)

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
