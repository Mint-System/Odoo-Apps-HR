# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.misc import format_duration


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    overtime_rule_ids = fields.One2many(
        "hr.attendance.overtime.rule",
        "leave_type_id",
        string="Linked Overtime Rules",
    )

    def _is_linked_overtime_type(self):
        """Return True if the type has its own balance from an overtime rule."""
        self.ensure_one()
        return bool(self.overtime_deductible and not self.requires_allocation and self.overtime_rule_ids)

    @api.depends("overtime_deductible", "requires_allocation", "overtime_rule_ids")
    @api.depends_context("request_type", "leave", "holiday_status_display_name", "employee_id")
    def _compute_display_name(self):
        """Show the balance of the time off type in the leave request."""
        res = super()._compute_display_name()
        if not self.requested_display_name() or self.env.context.get("request_type", "leave") == "allocation":
            return res
        employee = self.env["hr.employee"].browse(self.env.context.get("employee_id")).sudo()
        if not employee:
            return res
        balances = employee._get_overtime_leave_type_balances()[employee.id]
        for leave_type in self.filtered(lambda lt: lt._is_linked_overtime_type()):
            leave_type.display_name = "{name} ({count})".format(
                name=leave_type.name,
                count=self.env._(
                    "%s hours available",
                    format_duration(balances[leave_type.id]["balance"]),
                ),
            )
        return res

    def get_allocation_data(self, employees, target_date=None):
        """Add one dashboard tile per linked time off type."""
        res = super().get_allocation_data(employees, target_date)
        linked_types = self.filtered(lambda lt: lt._is_linked_overtime_type())
        if not linked_types:
            return res
        balances = employees._get_overtime_leave_type_balances()
        for employee in employees:
            # Replace the default tile (global total) by the own balance
            res[employee] = [info for info in res[employee] if info[3] not in linked_types.ids]
            for leave_type in linked_types:
                data = balances[employee.id][leave_type.id]
                res[employee].append(
                    (
                        leave_type.name,
                        {
                            "remaining_leaves": data["balance"],
                            "virtual_remaining_leaves": data["balance"],
                            # Not displayed for overtime tiles, but must be
                            # greater than zero, otherwise the dashboard hides
                            # the tile.
                            "max_leaves": max(data["earned"], 0.01),
                            "leaves_taken": data["taken"],
                            "virtual_leaves_taken": data["taken"],
                            "closest_allocation_remaining": 0,
                            "closest_allocation_expire": False,
                            "total_virtual_excess": 0,
                            "virtual_excess_data": {},
                            "request_unit": leave_type.request_unit,
                            "icon": leave_type.sudo().icon_id.url,
                            "allows_negative": leave_type.allows_negative,
                            "max_allowed_negative": leave_type.max_allowed_negative,
                            "overtime_deductible": True,
                            "employee_company": employee.company_id.id,
                        },
                        leave_type.requires_allocation,
                        leave_type.id,
                    )
                )
        return res
