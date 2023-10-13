from odoo import _, fields, models


class EmployeeFleet(models.Model):
    _inherit = "employee.fleet"

    expense_id = fields.Many2one(
        "hr.expense", tracked=True, readonly=True, ondelete="restrict", copy=False
    )

    def returned(self):
        res = super().returned()
        if self.private_usage:
            product = self.env.ref(
                "hr_expense_vehicle_request.product_product_vehicle_rental"
            )
            expense = self.env["hr.expense"].create(
                {
                    "name": _("Vehicle Rental %s") % self.name,
                    "employee_id": self.employee.id,
                    "product_id": product.id,
                    "unit_amount": self.trip,
                    "payment_mode": "company_account",
                    "reference": self.name,
                }
            )
            self.write({"expense_id": expense.id})
        return res
