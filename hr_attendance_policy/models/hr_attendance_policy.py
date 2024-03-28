from odoo import fields, models


class HRAttendancePolicy(models.Model):
    _name = "hr.attendance.policy"
    _description = "Attendance Policy"

    active = fields.Boolean(
        "Active", default=True, help="Indicates if the policy is active."
    )
    name = fields.Char("Name", required=True, help="The name of the attendance policy.")
    rule_ids = fields.One2many(
        "hr.attendance.rule",
        "policy_id",
        string="Rules",
        help="The set of rules that define this policy.",
    )
    warning_message = fields.Text(
        "Warning Message", help="A message to display if the policy is violated."
    )


class HRAttendanceRule(models.Model):
    _name = "hr.attendance.rule"
    _description = "Attendance Rule"

    policy_id = fields.Many2one(
        "hr.attendance.policy",
        required=True,
        help="The attendance policy this rule belongs to.",
    )
    min_work_hours = fields.Float(
        "Minimum Work Hours",
        help="The minimum number of work hours required by this rule.",
    )
    max_work_hours = fields.Float(
        "Maximum Work Hours",
        help="The maximum number of work hours allowed by this rule.",
    )
    min_delta = fields.Float(
        "Minimum Delta", help="The minimum acceptable difference in work hours."
    )
    period_days = fields.Integer(
        help="The number of days over which to apply this rule."
    )
