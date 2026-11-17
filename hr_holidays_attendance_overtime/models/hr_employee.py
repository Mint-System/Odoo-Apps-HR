# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_overtime_leave_type_balances(self):
        """Compute the balance per linked time off type.

        Credited: approved overtime lines that are compensable as time off and
        whose deciding rule is linked to a time off type. Negative lines from
        rules with a fixed amount of hours (e.g. 45 h per week) are ignored,
        they do not represent real missing hours. The hours of a rule with a
        weekly limit are already capped when the lines are generated.
        Taken: leaves of these types (all states except refused and cancelled).

        :return: {employee_id: {leave_type_id: {"earned": h, "taken": h, "balance": h}}}
        """
        result = defaultdict(lambda: defaultdict(lambda: {"earned": 0.0, "taken": 0.0, "balance": 0.0}))
        if not self.ids:
            return result

        lines = (
            self.env["hr.attendance.overtime.line"]
            .sudo()
            .search(
                [
                    ("compensable_as_leave", "=", True),
                    ("employee_id", "in", self.ids),
                    ("status", "=", "approved"),
                    ("overtime_leave_type_id", "!=", False),
                ]
            )
        )
        for line in lines:
            deciding_rule = line._get_deciding_rule()
            if line.manual_duration < 0 and not deciding_rule.expected_hours_from_contract:
                continue
            result[line.employee_id.id][line.overtime_leave_type_id.id]["earned"] += line.manual_duration

        for employee, leave_type, hours in (
            self.env["hr.leave"]
            .sudo()
            ._read_group(
                domain=[
                    ("holiday_status_id.overtime_deductible", "=", True),
                    ("holiday_status_id.requires_allocation", "=", False),
                    ("holiday_status_id.overtime_rule_ids", "!=", False),
                    ("employee_id", "in", self.ids),
                    ("state", "not in", ["refuse", "cancel"]),
                ],
                groupby=["employee_id", "holiday_status_id"],
                aggregates=["number_of_hours:sum"],
            )
        ):
            result[employee.id][leave_type.id]["taken"] += hours

        for employee_vals in result.values():
            for vals in employee_vals.values():
                vals["balance"] = vals["earned"] - vals["taken"]
        return result
