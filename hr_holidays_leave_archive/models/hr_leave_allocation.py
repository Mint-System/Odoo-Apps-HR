import logging
from odoo import models, fields
_logger = logging.getLogger(__name__)


class HolidaysAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    active = fields.Boolean(default=True)

    def toggle_active(self):
        for allocation in self:
            allocation.state = 'cancel'
            # Archive all related leaves
            leaves = self.env['hr.leave'].search([
                ('holiday_status_id', '=', allocation.holiday_status_id.id),
                ('employee_id', '=', allocation.employee_id.id),
            ])
            leaves.toggle_active()
            super(HolidaysAllocation, allocation).toggle_active()