import logging
from datetime import datetime, timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)
from dateutil.relativedelta import relativedelta


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def run_create_missing_attendances(self):
        employees = self.search([])
        employees._create_missing_attendances()

    def _create_missing_attendances(
        self,
        date_from=fields.Date.today() + relativedelta(days=-1),
        date_to=fields.Date.today() + relativedelta(days=-1),
    ):

        date_from = datetime.combine(date_from, datetime.min.time())
        date_to = datetime.combine(date_to, datetime.max.time())
        date_list = [
            date_from + timedelta(days=x) for x in range((date_to - date_from).days + 1)
        ]

        _logger.warning([date_from, date_to, date_list])

        for employee in self:

            # Get attendances
            attendances = self.env["hr.attendance"].search(
                [("employee_id", "=", employee.id), ("check_in", ">=", date_from)]
            )
            attendance_dates = (
                attendances.mapped(
                    lambda a: [a.check_in.date(), a.check_out.date()]
                    if a.check_out
                    else [a.check_in.date()]
                ).flat_map(list)
                if attendances
                else []
            )

            # Get leaves
            leaves = self.env["hr.leave"].search(
                [
                    ("employee_id", "=", employee.id),
                    "|",
                    ("date_from", ">=", date_from),
                    ("date_to", ">=", date_from),
                ]
            )
            leave_dates = (
                leaves.mapped(
                    lambda l: [l.date_from.date(), l.date_to.date()]
                    if l.date_to
                    else [l.date_from.date()]
                ).flat_map(list)
                if leaves
                else []
            )

            # Get public holidays
            calendar_leaves = self.env["resource.calendar.leaves"].search(
                [
                    ("calendar_id", "=", employee.resource_calendar_id.id),
                    ("resource_id", "=", False),
                    "|",
                    ("date_from", ">=", date_from),
                    ("date_to", "<=", date_from),
                ]
            )
            calendar_leave_dates = (
                calendar_leaves.mapped(
                    lambda cl: [cl.date_from.date(), cl.date_to.date()]
                    if cl.date_to
                    else [cl.date_from.date()]
                ).flat_map(list)
                if calendar_leaves
                else []
            )

            _logger.warning(
                [
                    attendances,
                    attendance_dates,
                ]
            )
            _logger.warning(
                [
                    leaves,
                    leave_dates,
                ]
            )
            _logger.warning(
                [
                    calendar_leaves,
                    calendar_leave_dates,
                ]
            )

            # Check every date in range
            for check_date in date_list:

                min_check_date = datetime.combine(check_date, datetime.min.time())
                max_check_date = datetime.combine(check_date, datetime.max.time())

                # Get working hours
                work_hours = employee.resource_calendar_id.get_work_hours_count(
                    min_check_date, max_check_date, False
                )

                is_attendance = check_date in attendance_dates
                is_leave = check_date in leave_dates
                is_calendar_leave = check_date in calendar_leave_dates

                if (
                    work_hours and
                    work_hours > 0
                    and not is_attendance
                    and not is_leave
                    and not is_calendar_leave
                ):
                    _logger.warning("Attenance Missing %s" % check_date)
