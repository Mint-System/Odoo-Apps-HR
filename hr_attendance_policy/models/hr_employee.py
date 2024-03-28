import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = "hr.employee"

    policy_ids = fields.Many2many(
        "hr.attendance.policy", string="Policies", compute="_compute_policies"
    )

    @api.depends()
    def _compute_policies(self):
        for employee in self:
            _logger.info(
                "Computing policies for employee %s with department_id %s and job_id %s",
                employee.name,
            )
            policies = self.env["hr.attendance.policy"].search([])
            employee.policy_ids = [(6, 0, policies.ids)]
