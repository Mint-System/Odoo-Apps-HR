import json
import logging
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _active_employee_domain(self):
        return []

    @api.model
    def cron_create_missing_attendances(self, logging=False):
        employees = self.search(self._active_employee_domain())
        employees.create_missing_attendances(logging=logging)

    def create_missing_attendances_employee(self, date_from, date_to, logging):
        """
        Create missing attendances for one employee.
        """
        self.ensure_one()
        employee = self
        missing_attendances = []

        # Get attendances - excluding the ones with check_out missing
        attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "=", employee.id),
                ("check_in", ">=", date_from),
                ("check_out", "!=", False),
            ]
        )
        attendance_dates = attendances.mapped("check_in") + attendances.mapped("check_out")
        attendance_dates = [dt.date() for dt in attendance_dates]

        # Get daily leaves
        leaves = self.env["hr.leave"].search(
            [
                "&",
                ("employee_id", "=", employee.id),
                ("holiday_status_id.ignore_missing_attendance", "=", False),
                "|",
                ("date_from", ">=", date_from),
                ("date_to", ">=", date_from),
            ]
        )

        # Get public holidays
        calendar_leaves = self.env["resource.calendar.leaves"].search(
            [
                "&",
                "&",
                "&",
                "|",
                ("resource_id", "=", False),
                ("company_id", "=", employee.company_id.id),
                ("calendar_id", "=", employee.resource_calendar_id.id),
                ("calendar_id", "=", False),
                "|",
                ("date_from", ">=", date_from),
                ("date_to", "<=", date_to),
            ]
        )

        # Check every date in range
        for days in range((date_to - date_from).days + 1):
            check_date = date_from + timedelta(days=days)

            min_check_date = datetime.combine(check_date, datetime.min.time())
            max_check_date = datetime.combine(check_date, datetime.max.time())

            # Get working hours
            work_hours = employee.resource_calendar_id.get_work_hours_count(min_check_date, max_check_date)

            # Execute checks
            is_attendance = check_date.date() in attendance_dates
            is_leave = leaves.filtered(
                lambda r: r.date_from <= check_date <= r.date_to
                or min_check_date <= r.date_from <= max_check_date
                or min_check_date <= r.date_to <= max_check_date
            )
            is_calendar_leave = calendar_leaves.filtered(
                lambda r: r.date_from <= check_date <= r.date_to
                or min_check_date <= r.date_from <= max_check_date
                or min_check_date <= r.date_to <= max_check_date
            )

            if logging:
                message = json.dumps(
                    {
                        "check_date": check_date,
                        "name": employee.name,
                        "company": employee.company_id.name,
                        "work_hours": work_hours,
                        "is_attendance": is_attendance,
                        "is_leave": is_leave,
                        "is_calendar_leave": is_calendar_leave,
                        "attendance_dates": attendance_dates,
                        "calendar_leaves": calendar_leaves.mapped("name"),
                        "condition": work_hours
                        and work_hours > 0
                        and not is_attendance
                        and not is_leave
                        and not is_calendar_leave,
                    },
                    indent=4,
                    default=str,
                )
                self.env["ir.logging"].sudo().create(
                    {
                        "name": "Create Missing Attendances: " + employee.name,
                        "type": "server",
                        "dbname": self._cr.dbname,
                        "level": "DEBUG",
                        "message": message,
                        "path": "",
                        "func": "",
                        "line": "",
                    }
                )

            if work_hours and work_hours > 0 and not is_attendance and not is_leave and not is_calendar_leave:
                attendance = self.env["hr.attendance"].create(
                    {
                        "employee_id": employee.id,
                        "check_in": check_date.replace(hour=8),
                        "check_out": check_date.replace(hour=8),
                        "is_missing_attendance": True,
                    }
                )
                attendance._update_overtime()
                missing_attendances.append(attendance)
        return missing_attendances

    def create_missing_attendances(self, date_from=None, date_to=None, logging=False):
        """
        Create missing attendances for all employees.
        """

        # Set default
        if date_from:
            date_from = datetime.combine(date_from, datetime.min.time())
        else:
            date_from = datetime.combine(fields.Date.today() + relativedelta(days=-1), datetime.min.time())

        if date_to:
            date_to = datetime.combine(date_to, datetime.max.time())
        else:
            date_to = datetime.combine(fields.Date.today() + relativedelta(days=-1), datetime.max.time())

        # Define minimum and maximum time
        date_from = datetime.combine(date_from, datetime.min.time())
        date_to = datetime.combine(date_to, datetime.max.time())

        missing_attendances = []
        for employee in self:
            missing_attendances += employee.create_missing_attendances_employee(date_from, date_to, logging)

        message = "%s missing attendances have been created." % len(missing_attendances)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Missing Attendances",
                "message": message,
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},  # Refresh the form
            },
        }
