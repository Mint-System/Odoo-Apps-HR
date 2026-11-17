# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrAttendanceOvertimeLine(models.Model):
    _inherit = "hr.attendance.overtime.line"

    overtime_leave_type_id = fields.Many2one(
        "hr.leave.type",
        string="Time Off Type",
        compute="_compute_overtime_leave_type_id",
        store=True,
        index=True,
        help="Time off type the hours of this line are credited to.",
    )

    @api.depends("rule_ids", "rule_ids.leave_type_id", "rule_ids.sequence")
    def _compute_overtime_leave_type_id(self):
        """Set the time off type of the deciding rule."""
        for line in self:
            line.overtime_leave_type_id = line._get_deciding_rule().leave_type_id

    def _get_deciding_rule(self):
        """Return the linked rule with the highest sequence.

        E.g. the weekly overtime rule is evaluated after the daily extra hours
        rule, hence its time off type wins for the overlapping hours.
        """
        self.ensure_one()
        rules = self.rule_ids.filtered("leave_type_id")
        return rules.sorted(lambda rule: (rule.sequence, rule.id))[-1:] if rules else rules
