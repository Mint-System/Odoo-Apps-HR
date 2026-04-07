import logging
import pytz
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time, timedelta

from odoo import api, models, fields
from odoo.tools import format_date

_logger = logging.getLogger(__name__)

def get_code(self, leave_type, company_id):
    if leave_type.code:
        return leave_type.code
    existing_codes = {
        lt.code.strip()
        for lt in self.env["hr.leave.type"].search(
            [
                "|",
                ("company_id", "=", company_id),
                ("company_id", "=", False)
            ]
        )
        if lt.code and lt.code.strip()
    }
    counter = 0
    
    new_code = "".join(word[0 : counter + 3] for word in leave_type.name.split() if word).upper()
    while new_code in existing_codes:
        counter += 1
        new_code = "".join(word[0 : counter + 3] for word in leave_type.name.split() if word).upper()
    leave_type.code = new_code

    return new_code

def _get_local_time(date, tz):
    return pytz.utc.localize(date).astimezone(tz)

def _get_last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)

def _get_overtime_totals(employee, start_date):
    today = fields.Date.today()
    one_month_earlier = today - relativedelta(months=1)

    # check if stored values can be taken
    if  one_month_earlier == start_date:
        overtime_last_month = employee.overtime_last_month or 0
        overtime_two_months_ago = employee.overtime_two_months_ago or 0
    else:# or caluclate
        last_day_of_previous_month = start_date - timedelta(days=1)
        last_day_of_this_month = _get_last_day_of_month(start_date)
        overtime_two_months_ago = sum(
            employee.overtime_ids.filtered(lambda overtime: overtime.date <= last_day_of_previous_month.date()).mapped(
                "duration"
            )
        )

        overtime_last_month = sum(
            employee.overtime_ids.filtered(lambda overtime: overtime.date <= last_day_of_this_month.date()).mapped(
                "duration"
            )
        )

    return overtime_last_month, overtime_two_months_ago

def get_holidays_allocations(self, employees):
    """Return FER leave allocations with calculated fields"""
    holiday_allocations = {}
    now = fields.Datetime.now()
    for employee in employees:
        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', employee.id),
            ('holiday_status_id.code', 'like', 'FER%'),
            ('state', '=', 'validate'),
        ])

        result = []
        for alloc in allocations:
            # Get approved leaves from this allocation
            leaves = self.env['hr.leave'].search([
                ('holiday_status_id', '=', alloc.holiday_status_id.id),
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
            ])

            # Taken leaves (past or present)
            used_leaves = leaves.filtered(lambda l: l.date_to <= now)

            # Planned leaves (future)
            planned_leaves = leaves.filtered(lambda l: l.date_from > now)

            # Calculate totals
            used_days = sum(used_leaves.mapped('number_of_days'))
            planned_days = sum(planned_leaves.mapped('number_of_days'))
            remaining_allocation = alloc.number_of_days - used_days - planned_days

            if remaining_allocation > 0:
                result.append({
                    'description': alloc.holiday_status_id.name,
                    'allocation': alloc.number_of_days,
                    'used': used_days,
                    'planned': planned_days,
                    'remaining': remaining_allocation,
                })
        holiday_allocations[employee.id] = result

    return holiday_allocations

def get_non_holiday_leaves(self, employees):
    """Return all leaves code not starting with 'FER' """

    non_holiday_leaves = {}
    now = fields.Datetime.now()
    for employee in employees:
        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),  # Only approved leaves
        ])

        result = []
        for leave in leaves:
            leave_type = leave.holiday_status_id
            if leave_type.code and leave_type.code.startswith('FER'):
                continue 

             # Find the allocation that granted this leave
            allocation = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', leave.employee_id.id),
                ('holiday_status_id', '=', leave.holiday_status_id.id),
                ('state', '=', 'validate'),
                ('number_of_days', '>', 0),
            ], limit=1)

            allocation_days = allocation.number_of_days if allocation else '-'

            date = leave.date_from.strftime('%d.%m.%Y') or ""
            if leave.date_from and leave.date_to and (leave.date_from.date() != leave.date_to.date()):
                date += f"-{leave.date_to.strftime('%d.%m.%Y')}"

            result.append({
                'description': leave.name,
                'leave_type': leave_type.name,
                'allocation': allocation_days,
                'used': leave.number_of_days,
                'date': date,
            })
        non_holiday_leaves[employee.id] = result

    return non_holiday_leaves



def get_leave_allocations(self, employees, start_date, end_date):
    """Get data on leave and allocations."""

    leave_codes = []
    for leave_type in self.env["hr.leave.type"].search(
        [("requires_allocation", "=", "yes"), ("company_id", "=", self.env.company.id)]
    ):
        code = get_code(self, leave_type, self.env.company.id)
        leave_codes.append(code)

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
            allocation_ids_per_type = allocation_ids.filtered(lambda alloc: alloc.holiday_status_id.code == leave_code and alloc.number_of_days > 0)
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



class ReportHrEmployee(models.AbstractModel):
    _inherit = "report.hr_employee_attendance_report.hr_employee"

    def get_months_pretty(self, dt):
        # current = dt.strftime("%B %Y")
        # prev = (dt.replace(day=1) - timedelta(days=1)).strftime("%B %Y")
        current = format_date(self.env, dt, date_format="MMMM yyyy")
        prev = format_date(self.env, dt.replace(day=1) - timedelta(days=1), date_format="MMMM yyyy")
        return current, prev

    @api.model
    def _get_report_values(self, docids, data=None):
        res = super()._get_report_values(docids, data)
        _logger.warning(f"res: {res}")
        _logger.warning(f"res summary: {res["summary"]}")

        now = fields.Datetime.now()
        # Last month default dates
        start_date = now + relativedelta(months=-1, day=1, hour=0, minute=0, second=0)
        end_date = now + relativedelta(day=1, hour=0, minute=0, second=0)

        # Check data for params from dialog
        if data and data.get("date_from"):
            start_date = datetime.strptime(data["date_from"], "%Y-%m-%d")
        if data and data.get("date_until"):
            end_date = datetime.strptime(data["date_until"], "%Y-%m-%d") + timedelta(days=1)
        if data.get("context", {}).get("active_ids"):
            docids = data["context"]["active_ids"]

        report_name = self._name

        if report_name == "report.hr_employee_attendance_report.res_users":
            employees = self.env["res.users"].browse(docids).mapped("employee_id")
        else:
            employees = self.env["hr.employee"].browse(docids)


        #  add allocations to report values
        holidays_allocations = get_holidays_allocations(self, employees)
        res["holidays_allocations"] = holidays_allocations

        non_holiday_leaves = get_non_holiday_leaves(self, employees)
        res["non_holiday_leaves"] = non_holiday_leaves
        res["date_as_of"] = now.strftime('%d.%m.%Y')
        current_month, previous_month = self.get_months_pretty(start_date)
        res["current_month"] = current_month
        res["previous_month"] = previous_month

        # overtime_balances = self._get_leaves_data(res)

        # Merge leaves data into summary records
        summary = res.get("summary", {})
        dates = res.get("dates", {})
        for employee_id, date_vals in dates.items():
            employee = self.env['hr.employee'].browse(employee_id)
            start_date = date_vals.get("start_date")
            if not start_date:
                continue

            overtime_last_month, overtime_two_months_ago = _get_overtime_totals(employee, start_date)

            summary.setdefault(employee_id, {})["overtime_last_month"] = round(overtime_last_month, 2)
            summary.setdefault(employee_id, {})["overtime_two_months_ago"] = round(overtime_two_months_ago, 2)
            summary.setdefault(employee_id, {})["overtime_balance"] = round(overtime_last_month - overtime_two_months_ago, 2)

        return res


    

    


