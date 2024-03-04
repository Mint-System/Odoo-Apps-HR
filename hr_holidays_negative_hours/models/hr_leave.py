import logging
from odoo import models
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _check_overtime_deductible(self, leaves):
        try:
            super()._check_overtime_deductible(leaves)
        except ValidationError:
            return True

    def action_draft(self):
        try:
            super().action_draft()
        except ValidationError:
            overtime_leaves = self.filtered("overtime_deductible")
            overtime_leaves.overtime_id.sudo().unlink()
            for leave in overtime_leaves:
                overtime = (
                    self.env["hr.attendance.overtime"]
                    .sudo()
                    .create(
                        {
                            "employee_id": leave.employee_id.id,
                            "date": leave.date_from,
                            "adjustment": True,
                            "duration": -1 * leave.number_of_hours_display,
                        }
                    )
                )
                leave.sudo().overtime_id = overtime.id
