from odoo import _, fields, models
from odoo.exceptions import ValidationError

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def _check_overtime_deductible(self, leaves):
        try:
            super()._check_overtime_deductible(leaves)
        except ValidationError:
            return

    def action_draft(self):
        super().action_draft()
        overtime_leaves = self.filtered(lambda l: l.overtime_deductible and l.state in ['draft', 'confirm'])
        for leave in overtime_leaves:
            if leave.overtime_id:
                leave.overtime_id.sudo().unlink()
                overtime = self.env['hr.attendance.overtime'].sudo().create({
                    'employee_id': leave.employee_id.id,
                    'date': leave.date_from,
                    'adjustment': True,
                    'duration': -1 * leave.number_of_hours_display
                })
                leave.sudo().overtime_id = overtime.id
