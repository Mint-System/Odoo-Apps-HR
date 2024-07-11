import logging
from datetime import datetime, time

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrAtttendanceOvertime(models.Model):
    _inherit = "hr.attendance.overtime"

    worked_hours = fields.Float(compute="_compute_policies", store=True, readonly=True)
    conflicting_policy_ids = fields.Many2many(
        "hr.attendance.policy",
        string="Conflicting Policies",
        compute="_compute_policies",
        store=True,
        help="The overtime records conflicts with these policies.",
    )

    @api.depends("duration")
    def _compute_policies(self):
        rule_ids = self.env["hr.attendance.rule"].search([])
        for overtime in self:

            # Get attendance records of overtime date
            checkin_from = datetime.combine(overtime.date, time.min)
            checkout_until = datetime.combine(overtime.date, time.max)
            attendance_ids = self.env["hr.attendance"].search(
                [
                    ("employee_id", "=", overtime.employee_id.id),
                    ("check_in", ">=", checkin_from),
                    ("check_out", "<=", checkout_until),
                ]
            )
            worked_hours = sum(attendance_ids.mapped("worked_hours"))

            # Check all rules against overtime records
            policy_ids = []
            for rule_id in rule_ids:
                # Check if any delta matches the minimum requirements
                delta_matched = any(
                    rule_id.min_delta <= delta
                    for delta in attendance_ids.mapped("delta_hours")
                )
                # If no delta matches continue with checks
                if not delta_matched:
                    if (
                        rule_id.min_worked_hours
                        <= worked_hours
                        < rule_id.max_worked_hours
                    ):
                        policy_ids.append(rule_id.policy_id.id)
                    if (
                        rule_id.min_worked_hours <= worked_hours
                        and rule_id.max_worked_hours == -1
                    ):
                        policy_ids.append(rule_id.policy_id.id)
                    if (
                        rule_id.min_worked_hours == -1
                        and worked_hours < rule_id.max_worked_hours
                    ):
                        policy_ids.append(rule_id.policy_id.id)

            overtime.conflicting_policy_ids = policy_ids if policy_ids else False
            overtime.worked_hours = worked_hours
