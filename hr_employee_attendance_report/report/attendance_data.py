import logging

from collections import defaultdict

import pytz
from markupsafe import Markup

from datetime import datetime, time, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.osv import expression

_logger = logging.getLogger(__name__)


def _daterange(start_date, end_date):
    """Return list of dates."""
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

def _get_leave_type_abbreviation(leave_type_name):
    return ''.join(word[0].upper() for word in leave_type_name.split())

def _get_local_time(date, tz):
    return pytz.utc.localize(date).astimezone(tz)

def get_attendances(self, employees, start_date, end_date):
    """Group attendances by user and day."""

    # Data mappings
    dates = {}
    attendances = {}
    summary = {}

    # Iterate on users
    for employee in employees:
        # Get statics
        hours_per_day = employee.resource_calendar_id.hours_per_day
        fixed_work_hours = False if hours_per_day == 0 else True
        company_hours_per_day = employee.company_id.resource_calendar_id.hours_per_day

        # Log time range
        dates[employee.id] = {}
        dates[employee.id]["start_date"] = start_date
        dates[employee.id]["end_date"] = end_date - timedelta(days=1)

        # Get all attendances and overtime in range
        attendance_ids = self.env["hr.attendance"].search(
            [
                ("employee_id", "=", employee.id),
                "&",
                ("check_in", "<=", end_date),
                ("check_out", ">=", start_date),
            ]
        )
        overtime_ids = self.env["hr.attendance.overtime"].search(
            [
                ("employee_id", "=", employee.id),
                "&",
                ("date", "<=", end_date),
                ("date", ">=", start_date),
            ]
        )

        # overtime_model = self.env['hr.attendance.overtime']
        # paid_out_field_exists = 'paid_out' in overtime_model._fields

        # domain = [
        #     ('employee_id', '=', employee.id),
        #     ('date', '<=', end_date),
        #     ('date', '>=', start_date)
        # ]

        # if paid_out_field_exists:
        #     domain.append(('paid_out', '=', True))
        #     overtime_paid_out_ids = overtime_model.search(domain)

        # Get leaves with from or to date in range
        from_domain = [("date_from", ">=", start_date), ("date_from", "<=", end_date)]
        to_domain = [("date_to", ">=", end_date), ("date_to", "<=", end_date)]
        domain = [
            ("calendar_id", "=", employee.resource_calendar_id.id),
            ("resource_id", "=", employee.resource_id.id),
        ]
        filters = expression.AND([domain, expression.OR([from_domain, to_domain])])
        leave_ids = self.env["resource.calendar.leaves"].search(filters)
        leave_hours = sum(leave_ids.holiday_id.mapped("number_of_hours_display"))
        _logger.warning("leave ids: %s", leave_ids)
        _logger.warning("leave hours: %s", leave_hours)
        

        # Update summary
        summary[employee.id] = {
            "fixed_work_hours": fixed_work_hours,
            "leave_hours": round(leave_hours, 2),
            "worked_hours": round(sum(attendance_ids.mapped("worked_hours")), 2),
            "overtime_total": round(employee.total_overtime, 2),
            # "overtime_paid_out_total": round(employee.total_overtime_paid_out, 2),
        }

        # For each date in range compute details
        attendances[employee.id] = []
        planned_hours = 0
        overtime = 0
        leaves_dict = {}
        for leave_type in self.env["hr.leave.type"].search([]):
            code = leave_type.code
            if not code:
                code = ''.join(word[0] for word in leave_type.name.split() if word).upper()
                leave_type.write({'code': code})
            leaves_dict[code] = 0.0

        for date in _daterange(start_date, end_date):
            # Get work hours
            min_check_date = datetime.combine(date, time.min)
            max_check_date = datetime.combine(date, time.max)
            work_hours = employee.resource_calendar_id.get_work_hours_count(min_check_date, max_check_date, True)
            planned_hours += work_hours

            # Get leave hours for this date
            active_leaves = leave_ids.filtered(
                lambda l: l.date_from < date < l.date_to
                or min_check_date <= l.date_from <= max_check_date
                or min_check_date <= l.date_to <= max_check_date
            )

            active_leaves_dict = defaultdict(float)
           
            for leave_code in leaves_dict.keys():
                leave_hours_per_leave = 0.0
                number_of_hours_per_leave = active_leaves.filtered(
                    lambda l: l.holiday_id.holiday_status_id.code == leave_code
                ).holiday_id.number_of_hours_display
                if number_of_hours_per_leave > company_hours_per_day:
                    leave_hours_per_leave = work_hours
                else:
                    leave_hours_per_leave = number_of_hours_per_leave

                active_leaves_dict[leave_code] += leave_hours_per_leave

            leave_hours = sum(active_leaves_dict.values())

            leave_types = " ".join([leave_code + ": " + str(round(leave_hours_per_leave, 2)) for leave_code, leave_hours_per_leave in active_leaves_dict.items() if leave_hours_per_leave > 0.0])

            # Get attendance hours for this date
            worked_hours = sum(
                attendance_ids.filtered(lambda a: min_check_date < a.check_in < max_check_date).mapped("worked_hours")
            )

            # Get time stamps for this date
            user_tz = pytz.timezone(self.env.context.get("tz") or "UTC")
            time_stamps = []

            for attendance in attendance_ids.filtered(
                lambda a: a.check_in.date() == date.date()
            ):
                time_stamps.append(
                    {
                        "check_in": attendance.check_in,
                        "check_out": attendance.check_out,
                    }
                )

            sorted_time_stamps = sorted(time_stamps, key=lambda x: x['check_in'])
            time_stamps_string = Markup(" ".join([f"{_get_local_time(ts['check_in'], user_tz).strftime('%H:%M')}-{_get_local_time(ts['check_out'], user_tz).strftime('%H:%M')}<br>" for ts in sorted_time_stamps]))

            # Get overtime hours for this date
            overtime_hours = sum(overtime_ids.filtered(lambda o: o.date == date.date()).mapped("duration"))
            overtime += overtime_hours

            # Create data entry
            attendances[employee.id].append(
                {
                    "date": date,
                    "weekday": date.strftime('%a'),
                    "planned_hours": round(work_hours, 2),
                    "leave_hours": round(leave_hours, 2),
                    "leave_types": leave_types,
                    "worked_hours": round(worked_hours, 2),
                    "diff_hours": round(worked_hours - (work_hours - leave_hours), 2),
                    "time_stamps": time_stamps_string,
                    "overtime": round(overtime_hours, 2),
                    "background_color": "lightgrey" if work_hours == 0 and fixed_work_hours else "none",
                }
            )

        # Update summary
        summary[employee.id]["planned_hours"] = round(planned_hours, 2)
        summary[employee.id]["overtime"] = round(overtime, 2)
        summary[employee.id]["overtime_calculated"] = round(summary[employee.id]["worked_hours"] - (summary[employee.id]["planned_hours"] - summary[employee.id]["leave_hours"]), 2)
        summary[employee.id]["leaves"] = leaves_dict
        
    return dates, attendances, summary


def get_leave_allocations(self, employees):
    """Get data on leave and allocations."""

    leave_codes = []
    for leave_type in self.env["hr.leave.type"].search([]):
        code = leave_type.code
        if not code:
            code = ''.join(word[0] for word in leave_type.name.split() if word).upper()
            leave_type.write({'code': code})
        
        leave_codes.append(code)

    # Data mappings
    leave_allocations = {}
    leave_allocations_per_type = defaultdict(dict)

    # Init statics
    now = fields.Datetime.now()

    # Iterate on users
    for employee in employees:
        # Get active allocations
        allocation_ids = self.env["hr.leave.allocation"].search(
            [
                ("employee_id", "=", employee.id),
                "|",
                ("date_to", ">=", now),
                ("date_from", "<=", now),
            ]
        )

        leave_allocations[employee.id] = allocation_ids

        # differentiate leave types
        for leave_code in leave_codes:
            leaves_per_type = {}
            allocation_ids_per_type = self.env["hr.leave.allocation"].search(
                [
                    ("holiday_status_id.code", "=", leave_code),
                    ("employee_id", "=", employee.id),
                    "|",
                    ("date_to", ">=", now),
                    ("date_from", "<=", now),
                ]
            )
            leaves_per_type["number_of_days"] = (
                sum(allocation_ids_per_type.mapped("number_of_days")) if allocation_ids_per_type else 0
            )
            leaves_per_type["leaves_taken"] = (
                sum(allocation_ids_per_type.mapped("leaves_taken")) if allocation_ids_per_type else 0
            )
            leaves_per_type["remaining_leaves_days"] = (
                sum(allocation_ids_per_type.mapped("remaining_leaves_days")) if allocation_ids_per_type else 0
            )
            leave_allocations_per_type[employee.id][leave_code] = leaves_per_type


    return leave_allocations, leave_allocations_per_type


def _get_report_values(self, docids, data=None, report_name=None):
    now = fields.Datetime.now()
    # Last month default dates
    start_date = now + relativedelta(months=-1, day=1, hour=0, minute=0, second=0)
    end_date = now + relativedelta(day=1, hour=0, minute=0, second=0)
    # Current month default dates
    # start_date = now + relativedelta(day=1, hour=0, minute=0, second=0)
    # end_date = now + relativedelta(month=5, day=1, hour=0, minute=0, second=0)

    # Check data for params from dialog
    if data and data.get("date_from"):
        start_date = datetime.strptime(data["date_from"], "%Y-%m-%d")
    if data and data.get("date_until"):
        end_date = datetime.strptime(data["date_until"], "%Y-%m-%d") + timedelta(days=1)
    if data.get("context", {}).get("active_ids"):
        docids = data["context"]["active_ids"]

    # Browse documents
    if report_name == "report.hr_employee_attendance_report.res_users":
        employees = self.env["res.users"].browse(docids).mapped("employee_id")
    else:
        employees = self.env["hr.employee"].browse(docids)

    dates, attendances, summary = get_attendances(self, employees, start_date, end_date)
    leave_allocations, leave_allocations_per_type = get_leave_allocations(self, employees)

    return {
        "doc_ids": docids,
        "doc_model": "hr.employee",
        "docs": employees,
        "dates": dates,
        "attendances": attendances,
        "summary": summary,
        "leave_allocations": leave_allocations,
        "leave_allocations_per_type": leave_allocations_per_type,
        "show_weekdays": data.get("show_weekdays", False),
        "show_diff_hours": data.get("show_diff_hours", False),
    }
