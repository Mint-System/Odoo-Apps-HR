import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = "hr.leave"

    compensate_overtime = fields.Boolean(related="holiday_status_id.compensate_overtime")
    compensate_overtime_id = fields.Many2one(
        "hr.attendance.overtime",
        string="Extra Hours Compensation",
    )

    def _check_overtime_deductible(self, leaves):
        """
        Skip this check for leaves of type extra hours.
        """
        holiday_status_extra_hours_id = self.env.ref("hr_holidays_attendance.holiday_status_extra_hours")
        for leave in leaves.filtered(lambda leave: leave.holiday_status_id == holiday_status_extra_hours_id):
            if not leave.overtime_deductible:
                leave.sudo().overtime_id.unlink()
                continue
            employee = leave.employee_id.sudo()
            duration = leave.number_of_hours
            if not leave.sudo().overtime_id:
                leave.sudo().overtime_id = (
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
        super()._check_overtime_deductible(
            leaves.filtered(lambda leave: leave.holiday_status_id != holiday_status_extra_hours_id)
        )

    def _create_overtime_entry(self):
        """
        Create and link overtime entry.
        """
        self.ensure_one()
        if not self.compensate_overtime_id and self.compensate_overtime:
            self.sudo().compensate_overtime_id = (
                self.env["hr.attendance.overtime"]
                .sudo()
                .create(
                    {
                        "employee_id": self.employee_id.id,
                        "date": self.date_from,
                        "adjustment": True,
                        "duration": -1 * self.number_of_hours,
                    }
                )
            )

    def write(self, vals):
        """
        Create and update linked overtime entry.
        """
        res = super().write(vals)
        for leave in self.sudo().filtered(
            lambda leave: leave.compensate_overtime and leave.state not in ["refuse", "cancel"]
        ):
            leave._create_overtime_entry()
            leave_duration = leave.number_of_hours
            overtime_duration = leave.compensate_overtime_id.sudo().duration
            if overtime_duration != leave_duration:
                leave.compensate_overtime_id.sudo().duration = -1 * leave_duration
        return res

    def action_refuse(self):
        """
        Delete linked overtime entry when leave is refused.
        """
        res = super().action_refuse()
        self.filtered("compensate_overtime").compensate_overtime_id.sudo().unlink()
        return res

    def unlink(self):
        self.sudo().compensate_overtime_id.unlink()
        return super().unlink()
