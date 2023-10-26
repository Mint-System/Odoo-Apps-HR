import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrExpense(models.Model):
    _inherit = "hr.expense"

    request_ids = fields.One2many("employee.fleet", "expense_id")
    request_count = fields.Integer("Requests", compute="_compute_request_count")

    @api.depends("request_ids")
    def _compute_request_count(self):
        for expense in self:
            expense.request_count = len(expense.request_ids)

    def view_vehicle_requests(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Vehicle Requests",
            "view_mode": "tree",
            "res_model": "employee.fleet",
            "domain": [("expense_id", "=", self.id)],
            "context": "{'create': False}",
        }

    def _create_sheet_from_expenses(self):
        """Set fleet owner as manager."""
        res = super()._create_sheet_from_expenses()

        if self.request_ids and self.request_ids[0].vehicle_id.manager_id:
            res.write({"user_id": self.request_ids[0].vehicle_id.manager_id.id})

        return res
