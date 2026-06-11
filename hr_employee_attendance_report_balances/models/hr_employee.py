# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    overtime_last_month = fields.Float(
        string="Overtime Last Month", help="Total overtime hours for the previous full month", readonly=True, store=True
    )
    overtime_two_months_ago = fields.Float(
        string="Overtime Two Months Ago",
        help="Total overtime hours for the month before last",
        readonly=True,
        store=True,
    )

    @api.model
    def _cron_update_overtime_last_two_months(self):
        return self.action_update_overtime_last_two_months()

    def action_update_overtime_last_two_months(self):
        today = fields.Date.today()
        first_day_of_current_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day=1)
        last_day_of_two_months_ago = first_day_of_previous_month - timedelta(days=1)
        first_day_of_two_months_ago = last_day_of_two_months_ago.replace(day=1)

        employees = self.search([])

        for employee in employees:
            # Calculate last month total (full previous month)
            last_month_total = sum(
                self.env["hr.attendance.overtime"]
                .search(
                    [
                        ("employee_id", "=", employee.id),
                        ("date", ">=", first_day_of_previous_month),
                        ("date", "<=", last_day_of_previous_month),
                    ]
                )
                .mapped("duration")
            )

            # Calculate two months ago total (full month before previous month)
            two_months_ago_total = sum(
                self.env["hr.attendance.overtime"]
                .search(
                    [
                        ("employee_id", "=", employee.id),
                        ("date", ">=", first_day_of_two_months_ago),
                        ("date", "<=", last_day_of_two_months_ago),
                    ]
                )
                .mapped("duration")
            )

            employee.write(
                {
                    "overtime_last_month": last_month_total,
                    "overtime_two_months_ago": two_months_ago_total,
                }
            )

        return True
