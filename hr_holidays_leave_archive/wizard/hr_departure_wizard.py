import logging
from odoo import models, fields
_logger = logging.getLogger(__name__)


class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    def action_register_departure(self):
        # Archive all related leave allocations
        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', self.employee_id.id)
        ])
        allocations.toggle_active()
        return super(HrDepartureWizard, self).action_register_departure()
