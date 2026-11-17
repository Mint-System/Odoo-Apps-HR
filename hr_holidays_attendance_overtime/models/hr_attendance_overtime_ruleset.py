# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrAttendanceOvertimeRuleset(models.Model):
    _inherit = "hr.attendance.overtime.ruleset"

    name = fields.Char(required=True, translate=True)
    employee_count = fields.Integer(compute="_compute_employee_count")

    def _compute_employee_count(self):
        """Count the employees having this ruleset on their current version."""
        versions = (
            self.env["hr.version"]
            .sudo()
            ._read_group(
                [("ruleset_id", "in", self.ids)],
                groupby=["ruleset_id"],
                aggregates=["__count"],
            )
        )
        count_by_ruleset = {ruleset.id: count for ruleset, count in versions}
        for ruleset in self:
            ruleset.employee_count = count_by_ruleset.get(ruleset.id, 0)

    def action_open_employees(self):
        """Open the employees that have this ruleset on their current version."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Employees"),
            "res_model": "hr.employee",
            "view_mode": "list,kanban,form",
            "domain": [("version_id.ruleset_id", "=", self.id)],
            "context": {"create": False},
        }
