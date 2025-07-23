import logging
from datetime import datetime

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _active_employee_domain(self):
        """
        Only check employees with running contract.
        """
        return [("contract_id.state", "=", "open")]

    def create_missing_attendances_employee(self, date_from, date_to, logging):
        """
        Replace date from with the start date of the contract.
        """
        if self.contract_id.state != "open":
            raise UserError(_(f"The employee {self.name} has no running contract."))
        date_from = datetime.combine(self.first_contract_date, datetime.min.time())
        return super().create_missing_attendances_employee(date_from, date_to, logging)
