import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    active = fields.Boolean(default=True)

    def toggle_active(self):
        for allocation in self:
            # allocation.state = 'cancel'
            # Archive all related leaves
            leaves = self.env["hr.leave"].search(
                [
                    ("holiday_status_id", "=", allocation.holiday_status_id.id),
                    ("employee_id", "=", allocation.employee_id.id),
                ]
            )
            leaves.toggle_active()
            super(HolidaysAllocation, allocation).toggle_active()


    
    
    def write(self, values):
        """ Bypass "You cannot archive an allocation which is in confirm or validate state."
            The original write() skips that check when context contains 'toggle_active'.
        """
        if "active" in values and not self.env.context.get("toggle_active"):
            return super(HolidaysAllocation, self.with_context(toggle_active=True)).write(values)
        return super(HolidaysAllocation, self).write(values)
