import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrAttendanceRule(models.Model):
    _name = "hr.attendance.rule"
    _description = "Attendance Rule"

    policy_id = fields.Many2one(
        "hr.attendance.policy",
        required=True,
        help="The attendance policy this rule belongs to.",
    )
    active = fields.Boolean(related="policy_id.active")
    min_worked_hours = fields.Float(
        "Minimum Worked Hours",
        help="Match minimum amount of worked hours.",
    )
    max_worked_hours = fields.Float(
        "Maximum Worked Hours",
        help="Match maximum amount of worked hours.",
    )
    min_delta = fields.Float(
        "Minimum Delta", help="The minimum acceptable difference in work hours."
    )
