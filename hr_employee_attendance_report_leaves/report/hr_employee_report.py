import logging
from collections import defaultdict
from datetime import datetime, time

import pytz

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


def _get_local_time(date, tz):
    return pytz.utc.localize(date).astimezone(tz)


def get_code(self, leave_type, company_id):
    if leave_type.code:
        return leave_type.code
    existing_codes = {
        lt.code.strip()
        for lt in self.env["hr.leave.type"].search(["|", ("company_id", "=", company_id), ("company_id", "=", False)])
        if lt.code and lt.code.strip()
    }
    counter = 0

    new_code = "".join(word[0 : counter + 3] for word in leave_type.name.split() if word).upper()
    while new_code in existing_codes:
        counter += 1
        new_code = "".join(word[0 : counter + 3] for word in leave_type.name.split() if word).upper()
    leave_type.code = new_code

    return new_code


class ReportHrEmployee(models.AbstractModel):
    _inherit = "report.hr_employee_attendance_report.hr_employee"

    @api.model
    def _get_report_values(self, docids, data=None):
        res = super()._get_report_values(docids, data)

        leaves = self._get_leaves_data(res)

        # Merge leaves data into attendance records
        attendances = res.get("attendances", {})
        for employee_id, attendance_list in attendances.items():
            employee_leaves = leaves.get(employee_id, [])
            for i, attendance in enumerate(attendance_list):
                if i < len(employee_leaves):
                    attendance["leave_types"] = employee_leaves[i].get("lt", "")
                else:
                    attendance["leave_types"] = ""

        return res

    def _get_leaves_data(self, res):
        leaves_dict = {}
        user_tz = pytz.timezone(self.env.context.get("tz") or "UTC")
        all_attendances = res.get("attendances")
        dates = res.get("dates")
        if all_attendances and dates:
            for key, value in all_attendances.items():
                employee_id = key
                employee = self.env["hr.employee"].browse(employee_id)
                leaves_dict[employee_id] = []
                company_hours_per_day = employee.company_id.resource_calendar_id.hours_per_day
                domain = [
                    ("calendar_id", "=", employee.resource_calendar_id.id),
                    ("resource_id", "=", employee.resource_id.id),
                ]

                leave_types_dict = {}
                leave_ids = self.env["resource.calendar.leaves"].search(domain)
                for leave_type in self.env["hr.leave.type"].search(
                    [
                        "|",
                        ("company_id", "=", employee.company_id.id),
                        ("company_id", "=", False),
                    ]
                ):
                    # for leave_type in self.env["hr.leave.type"].search([("company_id", "=", employee.company_id.id)]):
                    code = get_code(self, leave_type, employee.company_id.id)
                    display_name = leave_type.display_name
                    leave_types_dict[code] = 0.0

                for att in value:
                    date = att.get("date")
                    dt = fields.Datetime.to_datetime(date)
                    min_check_date = datetime.combine(dt, time.min)
                    max_check_date = datetime.combine(dt, time.max)
                    work_hours = employee.resource_calendar_id.get_work_hours_count(
                        min_check_date, max_check_date, True
                    )

                    active_leaves = leave_ids.filtered(
                        lambda l: l.date_from < dt < l.date_to
                        or min_check_date <= l.date_from <= max_check_date
                        or min_check_date <= l.date_to <= max_check_date
                    )

                    active_leaves_dict = defaultdict(float)

                    for leave_code in leave_types_dict.keys():
                        leave_hours_per_leave = 0.0
                        number_of_hours_per_leave = active_leaves.filtered(
                            lambda l: l.holiday_id.holiday_status_id.code == leave_code
                        ).holiday_id.number_of_hours
                        if number_of_hours_per_leave > company_hours_per_day:
                            leave_hours_per_leave = work_hours
                        else:
                            leave_hours_per_leave = number_of_hours_per_leave

                        active_leaves_dict[leave_code] += leave_hours_per_leave

                    leave_types = " ".join(
                        [
                            leave_code + ": " + str(round(leave_hours_per_leave, 2))
                            for leave_code, leave_hours_per_leave in active_leaves_dict.items()
                            if leave_hours_per_leave > 0.0
                        ]
                    )

                    leave_data_dict = {"date": date, "lt": leave_types}
                    leaves_dict[employee_id].append(leave_data_dict)

        return leaves_dict
