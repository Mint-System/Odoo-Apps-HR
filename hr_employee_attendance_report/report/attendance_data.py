import logging
from collections import defaultdict
from datetime import date, datetime, time, timedelta

import pytz
from dateutil.relativedelta import relativedelta
from markupsafe import Markup

from odoo import fields
from odoo.osv import expression
from odoo.tools import format_date

_logger = logging.getLogger(__name__)


def _daterange(start_date, end_date):
    """Return list of dates."""
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def _get_leave_type_abbreviation(leave_type_name):
    return "".join(word[0].upper() for word in leave_type_name.split())


def _get_local_time(date, tz):
    return pytz.utc.localize(date).astimezone(tz)


def _get_last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def _get_overtime_total_up_to_previous_month(employee, start_date):
    last_day_of_previous_month = start_date - timedelta(days=1)
    _logger.info("last_day_of_previous_month %s", last_day_of_previous_month)

    if employee.company_id.hr_attendance_overtime:
        total_overtime_up_to_previous_month = sum(
            employee.overtime_ids.filtered(lambda overtime: overtime.date <= last_day_of_previous_month.date()).mapped(
                "duration"
            )
        )
    else:
        total_overtime_up_to_previous_month = 0
    _logger.info("total_overtime_up_to_previous_month %s", total_overtime_up_to_previous_month)
    return total_overtime_up_to_previous_month


def _get_glz_up_to_previous_month(self, employee, start_date):
    last_day_of_previous_month = start_date - timedelta(days=1)
    domain = [
        ("calendar_id", "=", employee.resource_calendar_id.id),
        ("resource_id", "=", employee.resource_id.id),
        ("date_to", "<=", last_day_of_previous_month.date()),
    ]
    leave_ids = self.env["resource.calendar.leaves"].search(domain)
    glz_leaves = sum(
        leave_ids.filtered(lambda l: l.holiday_id.holiday_status_id.code == "GLZ").mapped(
            "holiday_id.number_of_hours_display"
        )
    )
    return glz_leaves


def _get_overtime_total_up_to_this_month(employee, start_date):
    last_day_of_this_month = _get_last_day_of_month(start_date)
    _logger.info("last_day_of_this_month %s", last_day_of_this_month)

    if employee.company_id.hr_attendance_overtime:
        total_overtime_up_to_this_month = sum(
            employee.overtime_ids.filtered(lambda overtime: overtime.date <= last_day_of_this_month.date()).mapped(
                "duration"
            )
        )
    else:
        total_overtime_up_to_this_month = 0
    _logger.info("total_overtime_up_to_this_month %s", total_overtime_up_to_this_month)
    return total_overtime_up_to_this_month


def _get_glz_up_to_this_month(self, employee, start_date):
    last_day_of_this_month = _get_last_day_of_month(start_date)
    domain = [
        ("calendar_id", "=", employee.resource_calendar_id.id),
        ("resource_id", "=", employee.resource_id.id),
        ("date_to", "<=", last_day_of_this_month.date()),
    ]
    leave_ids = self.env["resource.calendar.leaves"].search(domain)
    glz_leaves = sum(
        leave_ids.filtered(lambda l: l.holiday_id.holiday_status_id.code == "GLZ").mapped(
            "holiday_id.number_of_hours_display"
        )
    )
    return glz_leaves


def get_code(self, leave_type, company_id):
    existing_codes = set(
        lt.code
        for lt in self.env["hr.leave.type"].search(
            [("requires_allocation", "=", "yes"), ("company_id", "=", company_id)]
        )
    )
    _logger.info("### existing_codes %s", existing_codes)
    counter = 0
    if leave_type.code:
        return leave_type.code
    new_code = "".join(word[0 : counter + 1] for word in leave_type.name.split() if word).upper()
    while new_code in existing_codes:
        counter += 1
        new_code = "".join(word[0 : counter + 1] for word in leave_type.name.split() if word).upper()
    _logger.info("### new_code %s", new_code)

    return new_code


def get_attendances(self, employees, start_date, end_date):
    """Group attendances by user and day."""

    # Data mappings
    dates = {}
    attendances = {}
    summary = {}

    show_paid_out_overtime = self.env.context.get("show_paid_out_overtime", False)

    # Iterate on users
    for employee in employees:
        _logger.warning(f"### START DATE: {start_date}")
        _logger.warning(f"### END DATE: {end_date}")
        # Get statics
        hours_per_day = employee.resource_calendar_id.hours_per_day
        fixed_work_hours = False if hours_per_day == 0 else True
        company_hours_per_day = employee.company_id.resource_calendar_id.hours_per_day

        # Log time range
        dates[employee.id] = {}
        dates[employee.id]["start_date"] = start_date
        dates[employee.id]["end_date"] = end_date - timedelta(days=1)

        dates[employee.id]["end_date_of_previous_month"] = start_date - timedelta(days=1)
        dates[employee.id]["month_and_year"] = start_date.strftime("%B %Y")
        dates[employee.id]["year"] = start_date.year

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

        if show_paid_out_overtime:
            overtime_paid_out_ids = self.env["hr.attendance.overtime"].search(
                [
                    ("employee_id", "=", employee.id),
                    ("paid_out", "=", True),
                    "&",
                    ("date", "<=", end_date),
                    ("date", ">=", start_date),
                ]
            )

        # Get leaves with from or to date in range
        from_domain = [("date_from", ">=", start_date), ("date_from", "<=", end_date)]
        to_domain = [("date_to", ">=", start_date), ("date_to", "<=", end_date)]
        domain = [
            ("calendar_id", "=", employee.resource_calendar_id.id),
            ("resource_id", "=", employee.resource_id.id),
        ]
        filters = expression.AND([domain, expression.OR([from_domain, to_domain])])
        leave_ids = self.env["resource.calendar.leaves"].search(filters)
        _logger.warning(f"leave ids: {leave_ids}")

        leave_hours = sum(leave_ids.holiday_id.mapped("number_of_hours_display"))

        _logger.warning(f"leave hours this month: {leave_hours}")

        # Update summary
        total_overtime_up_to_previous_month = round(_get_overtime_total_up_to_previous_month(employee, start_date), 2)
        total_overtime_up_to_this_month = round(_get_overtime_total_up_to_this_month(employee, start_date), 2)
        total_overtime_saldo = total_overtime_up_to_this_month - total_overtime_up_to_previous_month
        glz_up_to_previous_month = round(_get_glz_up_to_previous_month(self, employee, start_date), 2)
        glz_up_to_this_month = round(_get_glz_up_to_this_month(self, employee, start_date), 2)
        glz_saldo = glz_up_to_this_month - glz_up_to_previous_month
        overtime_and_glz_up_to_previous_month = total_overtime_up_to_previous_month - glz_up_to_previous_month
        overtime_and_glz_up_to_this_month = total_overtime_up_to_this_month - glz_up_to_this_month
        overtime_and_glz_saldo = total_overtime_saldo - glz_saldo
        _logger.warning(
            f"#### glz_up_to_previous_month: {glz_up_to_previous_month}, total_overtime_up_to_previous_month: {total_overtime_up_to_previous_month}, overtime_and_glz_up_to_previous_month: {overtime_and_glz_up_to_previous_month} "
        )

        summary[employee.id] = {
            "fixed_work_hours": fixed_work_hours,
            "leave_hours": round(leave_hours, 2),
            "worked_hours": round(sum(attendance_ids.mapped("worked_hours")), 2),
            "overtime_total": round(employee.total_overtime, 2),
            "total_overtime_up_to_previous_month": total_overtime_up_to_previous_month,
            "total_overtime_up_to_this_month": total_overtime_up_to_this_month,
            "glz_up_to_previous_month": glz_up_to_previous_month,
            "glz_up_to_this_month": glz_up_to_this_month,
            "glz_saldo": glz_saldo,
            "overtime_and_glz_up_to_previous_month": overtime_and_glz_up_to_previous_month,
            "overtime_and_glz_up_to_this_month": overtime_and_glz_up_to_this_month,
            "overtime_and_glz_saldo": overtime_and_glz_saldo,
        }

        if show_paid_out_overtime:
            summary[employee.id]["overtime_paid_out_total"] = round(employee.total_paid_out_overtime, 2)

        # For each date in range compute details
        attendances[employee.id] = []
        planned_hours = 0
        overtime = 0
        overtime_paid_out = 0
        leaves_dict = {}
        for leave_type in self.env["hr.leave.type"].search([("company_id", "=", employee.company_id.id)]):
            code = get_code(self, leave_type, employee.company_id.id)
            display_name = leave_type.display_name
            leaves_dict[code] = 0.0

        mb_counter = 0

        leave_hours_sum = 0

        glz_hours = 0
        glz_sum = 0

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
            missing_breaks_dict = defaultdict(float)

            for leave_code in leaves_dict.keys():
                leave_hours_per_leave = 0.0
                number_of_hours_per_leave = active_leaves.filtered(
                    lambda l: l.holiday_id.holiday_status_id.code == leave_code
                ).holiday_id.number_of_hours_display
                if number_of_hours_per_leave > company_hours_per_day:
                    leave_hours_per_leave = work_hours
                else:
                    leave_hours_per_leave = number_of_hours_per_leave

                _logger.warning(f"####### leave code: {leave_code}, hours: {leave_hours_per_leave}")
                active_leaves_dict[leave_code] += leave_hours_per_leave

                glz_hours = active_leaves_dict["GLZ"]

                # if leave_code == "GLZ":
                #     glz_hours = leave_hours_per_leave
                # else:
                #     active_leaves_dict[leave_code] += leave_hours_per_leave

                # if leave_code == "GLZ":
                #     glz_hours = active_leaves.filtered(
                #         lambda l: l.holiday_id.holiday_status_id.code == "GLZ"
                #     ).holiday_id.number_of_hours_display

                glz_sum += glz_hours
                _logger.warning(f"GLZ hours: {glz_hours}")

            # leave_hours = sum(active_leaves_dict.values())
            leave_hours = sum(value for key, value in active_leaves_dict.items() if key != "GLZ")

            leave_hours_sum += leave_hours

            leave_types = " ".join(
                [
                    leave_code + ": " + str(round(leave_hours_per_leave, 2))
                    for leave_code, leave_hours_per_leave in active_leaves_dict.items()
                    if leave_hours_per_leave > 0.0
                ]
            )
            _logger.warning(f"########## Date: {date}, leave_types: {leave_types}")

            # Get attendance hours for this date
            worked_hours = sum(
                attendance_ids.filtered(lambda a: min_check_date < a.check_in < max_check_date).mapped("worked_hours")
            )

            # Get time stamps for this date
            user_tz = pytz.timezone(self.env.context.get("tz") or "UTC")
            time_stamps = []

            for attendance in attendance_ids.filtered(
                lambda a: a.check_in.date() == date.date() and a.check_out - a.check_in > timedelta(seconds=3)
            ):
                time_stamps.append(
                    {
                        "check_in": attendance.check_in,
                        "check_out": attendance.check_out,
                    }
                )

            sorted_time_stamps = sorted(time_stamps, key=lambda x: x["check_in"])
            time_stamps_string = Markup(
                " ".join(
                    [
                        f"{_get_local_time(ts['check_in'], user_tz).strftime('%H:%M')}-{_get_local_time(ts['check_out'], user_tz).strftime('%H:%M')}<br>"
                        for ts in sorted_time_stamps
                    ]
                )
            )

            # Get overtime hours for this date
            overtime_hours = sum(overtime_ids.filtered(lambda o: o.date == date.date()).mapped("duration"))
            overtime += overtime_hours

            if show_paid_out_overtime:
                overtime_paid_out_hours = sum(
                    overtime_paid_out_ids.filtered(lambda o: o.paid_out and o.date == date.date()).mapped("duration")
                )
                overtime_paid_out += overtime_paid_out_hours

            missing_break = self.env["hr.missing.break"].search(
                [("employee_id", "=", employee.id), ("working_day", "=", date)]
            )

            if missing_break:
                mb_counter += 1
                missing_breaks_hours = 0.5
                mb = True
                leave_types = leave_types + " | Fehl. Pause" if leave_types else "Fehl. Pause"
            else:
                missing_breaks_hours = 0.0
                mb = False

            _logger.warning(f"mb: {mb}")

            attendances_data_dict = {
                "date": date,
                "weekday": format_date(self.env, date, date_format="EE"),
                "planned_hours": round(work_hours, 2),
                "leave_hours": round(leave_hours, 2),
                "leave_types": leave_types,
                "missing_break": mb,
                "worked_hours": round(worked_hours - missing_breaks_hours, 2),
                "diff_hours": round(worked_hours - missing_breaks_hours - (work_hours - leave_hours), 2),
                "time_stamps": time_stamps_string,
                "overtime": round(overtime_hours, 2),
                "background_color": "lightgrey" if work_hours == 0 and fixed_work_hours else "none",
            }
            if show_paid_out_overtime:
                attendances_data_dict["overtime_paid_out"] = round(overtime_paid_out_hours, 2)
                attendances_data_dict["show_paid_out"] = show_paid_out_overtime

            # Create data entry
            attendances[employee.id].append(attendances_data_dict)

        # Update summary
        summary[employee.id]["worked_hours"] = summary[employee.id]["worked_hours"] - mb_counter * 0.5
        summary[employee.id]["planned_hours"] = round(planned_hours, 2)
        summary[employee.id]["leave_hours_sum"] = round(leave_hours_sum, 2)
        summary[employee.id]["overtime"] = round(overtime, 2)
        summary[employee.id]["overtime_calculated"] = round(
            summary[employee.id]["worked_hours"]
            - (summary[employee.id]["planned_hours"] - summary[employee.id]["leave_hours_sum"]),
            # - glz_sum,
            2,
        )
        summary[employee.id]["overtime_paid_out"] = round(overtime_paid_out, 2)
        summary[employee.id]["leaves"] = leaves_dict
        summary[employee.id]["overtime_diff"] = round(
            summary[employee.id]["overtime_calculated"] - summary[employee.id]["total_overtime_up_to_previous_month"], 2
        )
        summary[employee.id]["show_paid_out"] = show_paid_out_overtime
        summary[employee.id]["overtime_without_paid_out"] = round(
            summary[employee.id]["overtime_calculated"] - (-summary[employee.id]["overtime_paid_out"]), 2
        )

        for att in attendances[employee.id]:
            _logger.warning(f"att data: {att['date']}, mb: {att['missing_break']}")

    return dates, attendances, summary


def get_unallocated_leaves(self, employees, start_date, end_date):
    unallocated_leaves = {}
    for employee in employees:
        unallocated_leaves[employee.id] = defaultdict(float)
        leaves = self.env["hr.leave"].search(
            [
                ("employee_id", "=", employee.id),
                ("state", "=", "validate"),
                ("holiday_status_id.requires_allocation", "=", "no"),
                ("date_from", "<=", end_date),
                ("date_to", ">=", start_date),
            ]
        )

        for leave in leaves:
            code = leave.holiday_status_id.code
            if code and code != "GLZ":
                unallocated_leaves[employee.id][code] += leave.number_of_days

        return unallocated_leaves


def get_leave_allocations(self, employees, start_date, end_date):
    """Get data on leave and allocations."""

    leave_codes = []
    for leave_type in self.env["hr.leave.type"].search(
        [("requires_allocation", "=", "yes"), ("company_id", "=", self.env.company.id)]
    ):
        code = get_code(self, leave_type, self.env.company.id)
        leave_codes.append(code)

    _logger.info("leave code %s", leave_codes)
    # Data mappings
    leave_allocations = {}
    # leave_allocations_per_type = defaultdict(dict)
    leave_allocations_per_type = {}

    # Init statics
    now = fields.Datetime.now()

    # Iterate on users
    for employee in employees:
        # Get active allocations

        # search domain
        domain = [
            ("state", "=", "validate"),
            ("employee_id", "=", employee.id),
        ]

        if start_date.year == now.year:
            # active allocations
            domain += [
                ("date_from", "<=", now),
                ("date_to", ">=", now),
            ]
        else:
            # allocations from last year
            last_year_start = date(now.year - 1, 1, 1)
            last_year_end = date(now.year - 1, 12, 31)

            domain += [
                ("date_from", ">=", last_year_start),
                ("date_from", "<=", last_year_end),
            ]

        allocation_ids = self.env["hr.leave.allocation"].search(domain)

        leave_allocations[employee.id] = allocation_ids
        leave_allocations_per_type_per_employee = []

        # differentiate leave types
        for leave_code in leave_codes:
            leaves_per_type = {}
            # domain += [
            #     ("holiday_status_id.code", "=", leave_code),
            # ]
            # allocation_ids_per_type = self.env["hr.leave.allocation"].search(
            #     domain
            # )
            allocation_ids_per_type = allocation_ids.filtered(lambda alloc: alloc.holiday_status_id.code == leave_code)
            if allocation_ids_per_type:
                leaves_per_type["code"] = leave_code
                leaves_per_type["display_name"] = allocation_ids_per_type.mapped("holiday_status_id").display_name
                leaves_per_type["number_of_days"] = (
                    sum(allocation_ids_per_type.mapped("number_of_days")) if allocation_ids_per_type else 0
                )
                leaves_per_type["number_of_days_display"] = (
                    sum(allocation_ids_per_type.mapped("number_of_days_display")) if allocation_ids_per_type else 0
                )
                leaves_per_type["number_of_hours_display"] = (
                    sum(allocation_ids_per_type.mapped("number_of_hours_display")) if allocation_ids_per_type else 0
                )
                leaves_per_type["leaves_taken"] = (
                    sum(allocation_ids_per_type.mapped("leaves_taken")) if allocation_ids_per_type else 0
                )
                leaves_per_type["remaining_leaves_days"] = (
                    sum(allocation_ids_per_type.mapped("remaining_leaves_days")) if allocation_ids_per_type else 0
                )
                # leave_allocations_per_type[employee.id][leave_code] = leaves_per_type
                _logger.info("leaves_per_type %s", leaves_per_type)
                leave_allocations_per_type_per_employee.append(leaves_per_type)

        leave_allocations_per_type[employee.id] = leave_allocations_per_type_per_employee

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
    leave_allocations, leave_allocations_per_type = get_leave_allocations(self, employees, start_date, end_date)
    unallocated_leaves = get_unallocated_leaves(self, employees, start_date, end_date)
    _logger.warning(f"##### unallocated_leaves: {unallocated_leaves}")

    _logger.warning("### context: %s", self.env.context)
    show_allocation = self.env.context.get("show_allocation", True)

    return {
        "doc_ids": docids,
        "doc_model": "hr.employee",
        "docs": employees,
        "dates": dates,
        "attendances": attendances,
        "summary": summary,
        "leave_allocations": leave_allocations,
        "leave_allocations_per_type": leave_allocations_per_type,
        "unallocated_leaves": unallocated_leaves,
        "show_weekdays": data.get("show_weekdays", True),
        "show_diff_hours": data.get("show_diff_hours", True),
        "show_odoo_overtimes": data.get("show_odoo_overtimes", False),
        "show_allocation": show_allocation,
    }
