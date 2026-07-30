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


    # def _get_default_expense_sheet_values(self):
    #     values = super()._get_default_expense_sheet_values()
    #     if self.request_ids and self.request_ids[0].vehicle_id.manager_id:
    #         value = {
    #             "user_id": self.request_ids[0].vehicle_id.manager_id.id
    #         }
    #         values.append(value)
    #     return values


    def _get_default_expense_sheet_values(self):
        """Generate expense sheet values including the vehicle manager."""
        values = super()._get_default_expense_sheet_values()

        # Safe navigation: [:1] avoids IndexError if request_ids is empty
        request = self.request_ids[:1]
        vehicle_manager = request.vehicle_id.manager_id
        if vehicle_manager and 'user_id' in self.env['hr.expense.sheet']._fields:
            for vals in values:
                vals['user_id'] = vehicle_manager.id

        _logger.warning(f"####### values: {values}")

        return values


