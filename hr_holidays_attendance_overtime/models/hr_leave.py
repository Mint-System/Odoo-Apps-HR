# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import ValidationError


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _check_overtime_deductible(self, leaves):
        """Check the per time off type balance instead of the global extra hours.

        Leaves of a type linked to an overtime rule must not exceed the balance
        of that time off type.
        """
        super()._check_overtime_deductible(leaves)
        linked_leaves = leaves.filtered(
            lambda leave: leave.overtime_deductible
            and leave.holiday_status_id.overtime_rule_ids
            and leave.state not in ("refuse", "cancel")
        )
        if not linked_leaves:
            return
        balances = linked_leaves.employee_id._get_overtime_leave_type_balances()
        for leave in linked_leaves:
            balance = balances[leave.employee_id.id][leave.holiday_status_id.id]["balance"]
            if balance < -0.001:
                raise ValidationError(
                    self.env._(
                        "Not enough balance for %(type)s: the balance after this request would be %(balance).2f h.",
                        type=leave.holiday_status_id.name,
                        balance=balance,
                    )
                )
