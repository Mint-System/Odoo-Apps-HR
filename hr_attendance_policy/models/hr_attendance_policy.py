import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrAttendancePolicy(models.Model):
    _name = "hr.attendance.policy"
    _description = "Attendance Policy"

    active = fields.Boolean(default=True, help="Indicates if the policy is active.")
    name = fields.Char(required=True, help="The name of the attendance policy.")
    description = fields.Text(elp="A description of the attendance policy.")
    rule_ids = fields.One2many(
        "hr.attendance.rule",
        "policy_id",
        string="Rules",
        help="The set of rules that define this policy.",
    )
