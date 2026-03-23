import logging
import pytz
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time, timedelta

from odoo import api, models, fields

_logger = logging.getLogger(__name__)

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



class ReportHrEmployee(models.AbstractModel):
    _inherit = "report.hr_employee_attendance_report.hr_employee"

    @api.model
    def _get_report_values(self, docids, data=None):
        res = super()._get_report_values(docids, data)
        _logger.warning(f"res: {res}")
        _logger.warning(f"res summary: {res["summary"]}")


        #overtime_balances = self._get_leaves_data(res)

        # Merge leaves data into summary records
        summary = res.get("summary", {})
        dates = res.get("dates", {})
        for employee_id, date_vals in dates.items():
            _logger.warning(f"### summary: {summary}")
            employee = self.env['hr.employee'].browse(employee_id)
            start_date = date_vals.get("start_date")
            if not start_date:
                continue

            overtime_last_month, overtime_two_months_ago = _get_overtime_totals(employee, start_date)

            summary.setdefault(employee_id, {})["overtime_last_month"] = round(overtime_last_month, 2)
            summary.setdefault(employee_id, {})["overtime_two_months_ago"] = round(overtime_two_months_ago, 2)
            summary.setdefault(employee_id, {})["overtime_balance"] = round(overtime_last_month - overtime_two_months_ago, 2)

        _logger.warning(f"res summary after merge overtime: {res["summary"]}")
        return res

    


