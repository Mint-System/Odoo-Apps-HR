from odoo import api, models


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    @api.depends("employee_id", "employee_id.department_id")
    def _compute_from_employee_id(self):
        for sheet in self:
            # Always keep these two in sync with the employee
            sheet.address_id = sheet.employee_id.sudo().address_home_id
            sheet.department_id = sheet.employee_id.department_id

            # Only assign user_id if not set
            # This preserves vehicle manager passed from _get_default_expense_sheet_values
            if not sheet.user_id:
                sheet.user_id = sheet.employee_id.expense_manager_id or sheet.employee_id.parent_id.user_id
