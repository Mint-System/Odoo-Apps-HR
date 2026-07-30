import logging
from datetime import datetime, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.tools.misc import format_date

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = "hr.leave"

    attendance_ids = fields.One2many("hr.attendance", "leave_id")
    attendance_count = fields.Integer(compute="_compute_attendance_count")
    record_as_attendance = fields.Boolean(related="holiday_status_id.record_as_attendance")
    calendar_id = fields.Many2one("resource.calendar", compute="_compute_calendar_id", store=True)

    def name_get(self):
        res = []
        for leave in self:
            start_date = datetime.combine(leave.request_date_from, datetime.min.time())
            end_date = datetime.combine(leave.request_date_to, datetime.max.time())
            if leave.employee_id:
                target = leave.employee_id.name
            else:
                target = ", ".join(leave.employee_ids.mapped("name"))
            if leave.holiday_status_id.record_as_attendance:
                res.append(
                    (
                        leave.id,
                        _(
                            "%(person)s on %(leave_type)s: %(duration).2f hours on %(date)s",
                            person=target,
                            leave_type=leave.holiday_status_id.name,
                            duration=leave.calendar_id.get_work_hours_count(start_date, end_date),
                            date=format_date(self.env, start_date) or "",
                        ),
                    )
                )
            else:
                res.append((leave.id, super().name_get()[0][1]))
        return res

    @api.depends("attendance_ids")
    def _compute_attendance_count(self):
        for leave in self:
            leave.attendance_count = len(leave.attendance_ids)

    def action_attendance_view(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.attendance",
            "view_mode": "list,form",
            "domain": [("id", "in", self.attendance_ids.ids)],
        }

    @api.depends("holiday_status_id", "request_date_from", "request_date_to", "employee_id")
    def _compute_calendar_id(self):
        """
        If leave type calendar is set and leave hours is not greather than max hours,
        return that calendar otherwhise return employee calendar.
        """
        for rec in self:
            if not rec.request_date_from or not rec.request_date_to:
                rec.calendar_id = rec.employee_id.resource_calendar_id
                continue

            start_date = datetime.combine(rec.request_date_from, datetime.min.time())
            end_date = datetime.combine(rec.request_date_to, datetime.max.time())

            if rec.holiday_status_id.calendar_id:
                calendar_hours = rec.holiday_status_id.calendar_id.get_work_hours_count(
                    start_date,
                    end_date,
                    compute_leaves=False,
                )
                if rec.holiday_status_id.calendar_max_hours == 0 or (
                    calendar_hours <= rec.holiday_status_id.calendar_max_hours
                ):
                    rec.calendar_id = rec.holiday_status_id.calendar_id
                else:
                    rec.calendar_id = rec.employee_id.resource_calendar_id
            else:
                rec.calendar_id = rec.employee_id.resource_calendar_id

    def get_work_hour(self, date, day_period):
        """
        Get work hour from resource calendar.
        """
        self.ensure_one()
        dayofweek = date.weekday()
        work_hour_id = self.env["resource.calendar.attendance"].search(
            [
                ("calendar_id", "=", self.calendar_id.id),
                ("dayofweek", "=", dayofweek),
                ("day_period", "=", day_period),
                ("display_type", "=", False),
            ],
            limit=1,
        )
        return work_hour_id.hour_from

    def _get_work_intervals(self, date_from, date_to):
        """
        Get the work periods of the calendar between two naive datetimes.

        The intervals are taken from the resource calendar itself, so they
        contain neither lunch breaks nor the gap between the work periods of a
        day. Their durations therefore add up to the working time of that day,
        which is what has to be credited as attendance.

        Returns a list of (check_in, check_out, calendar attendance) tuples,
        with the datetimes as naive UTC, ready to be stored on an attendance.
        """
        self.ensure_one()
        user_tz = pytz.timezone(self.tz)
        resource = self.employee_id.resource_id
        intervals = self.calendar_id._attendance_intervals_batch(
            user_tz.localize(date_from),
            user_tz.localize(date_to),
            resources=resource,
        )[resource.id]
        return [
            (
                start.astimezone(pytz.utc).replace(tzinfo=None),
                stop.astimezone(pytz.utc).replace(tzinfo=None),
                attendance,
            )
            for start, stop, attendance in intervals
        ]

    def _get_leaves_on_public_holiday(self):
        """
        Overwrite method to allow leaves on public holiday.
        """
        return self.env["hr.leave"]

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super().create(vals_list)
    #     if res.state in ["validate1", "validate2"] and not res.attendance_ids:
    #         res.create_attendances()
    #     return res

    def create_attendances(self):
        """
        Create attendance entries if leave is recorded as attendance.
        """
        self.ensure_one()

        if self.record_as_attendance:
            user_tz = pytz.timezone(self.tz)

            # Convert to datetime
            start_date = datetime.combine(self.request_date_from, datetime.min.time())
            end_date = datetime.combine(self.request_date_to, datetime.max.time())

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

            # Create attendance based on unit type
            attendance_vals = []

            if not self.request_unit_half and not self.request_unit_hours:
                # Create an attendance for each work period of the calendar,
                # so a day with a lunch break results in two attendances.
                for check_in, check_out, _attendance in self._get_work_intervals(start_date, end_date):
                    attendance_vals.append(
                        {
                            "employee_id": self.employee_id.id,
                            "check_in": check_in,
                            "check_out": check_out,
                            "leave_id": self.id,
                        }
                    )

            elif self.request_unit_half:
                # Only keep the work periods of the requested half day.
                day_period = "morning" if self.request_date_from_period == "am" else "afternoon"
                for check_in, check_out, attendance in self._get_work_intervals(start_date, end_date):
                    if attendance.day_period != day_period:
                        continue
                    attendance_vals.append(
                        {
                            "employee_id": self.employee_id.id,
                            "check_in": check_in,
                            "check_out": check_out,
                            "leave_id": self.id,
                        }
                    )

            elif self.request_unit_hours:
                # Convert from user tz to utc
                check_in = user_tz.localize(start_date).astimezone(pytz.utc).replace(tzinfo=None)

                # Add hours to datetime
                check_out = check_in + timedelta(hours=self.request_time_hour_to)
                check_in = check_in + timedelta(hours=self.request_time_hour_from)

                attendance_vals.append(
                    {
                        "employee_id": self.employee_id.id,
                        "check_in": check_in,
                        "check_out": check_out,
                        "leave_id": self.id,
                    }
                )

            if not attendance_vals:
                _logger.warning(
                    "No attendance values generated for leave %s (employee: %s)",
                    self.display_name,
                    self.employee_id.name,
                )
                return
            self.env["hr.attendance"].sudo().create(attendance_vals)

    def unlink(self):
        self.sudo().attendance_ids.unlink()
        return super().unlink()

    def action_reset_confirm(self):
        res = super().action_reset_confirm()
        self.sudo().attendance_ids.unlink()
        return res

    def action_confirm(self):
        return super().action_confirm()

    def action_approve(self, check_state=True):
        res = super().action_approve(check_state)
        for leave in self.filtered(lambda l: l.record_as_attendance and not l.attendance_ids):
            leave.create_attendances()
        return res

    def action_validate(self, check_state=True):
        res = super().action_validate(check_state)
        for leave in self.filtered(lambda l: l.record_as_attendance and not l.attendance_ids):
            leave.create_attendances()
        return res

    def action_refuse(self):
        res = super().action_refuse()
        self.sudo().attendance_ids.unlink()
        return res

    def _force_cancel(self, *args, **kwargs):
        res = super()._force_cancel(*args, **kwargs)
        self.sudo().attendance_ids.unlink()
        return res
