import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = "hr.leave"

    compensate_overtime = fields.Boolean(
        related="holiday_status_id.compensate_overtime"
    )
    compensate_overtime_id = fields.Many2one(
        "hr.attendance.overtime",
        string="Extra Hours Compensation",
        groups="hr_holidays.group_hr_holidays_user",
    )

    def write(self, vals):
        res = super().write(vals)
        for leave in self.sudo().filtered("compensate_overtime_id"):
            if vals.get("state") in ["refuse"]:
                continue
            duration = leave.number_of_hours_display
            overtime_duration = leave.compensate_overtime_id.sudo().duration
            if overtime_duration != duration:
                leave.compensate_overtime_id.sudo().duration = -1 * duration
        return res

    def _check_overtime_deductible(self, leaves):
        res = super()._check_overtime_deductible(leaves)
        for leave in leaves:
            if not leave.compensate_overtime:
                continue
            employee = leave.employee_id.sudo()
            duration = leave.number_of_hours_display
            if not leave.compensate_overtime_id:
                leave.sudo().compensate_overtime_id = (
                    self.env["hr.attendance.overtime"]
                    .sudo()
                    .create(
                        {
                            "employee_id": employee.id,
                            "date": leave.date_from,
                            "adjustment": True,
                            "duration": -1 * duration,
                        }
                    )
                )
        return res

    def action_draft(self):
        overtime_leaves = self.filtered("compensate_overtime")
        res = super().action_draft()
        overtime_leaves.compensate_overtime_id.sudo().unlink()
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
            leave.sudo().compensate_overtime_id = overtime.id
        return res

    def unlink(self):
        self.sudo().compensate_overtime_id.unlink()
        return super().unlink()
