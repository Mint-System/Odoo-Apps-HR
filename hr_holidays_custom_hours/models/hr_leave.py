import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = "hr.leave"

    enable_custom_hours = fields.Boolean(
        related="holiday_status_id.enable_custom_hours"
    )
    custom_hours = fields.Float(inverse="_inverse_custom_hours")
    custom_overtime_id = fields.Many2one(
        "hr.attendance.overtime",
        string="Custom Hours Difference",
        groups="hr_holidays.group_hr_holidays_user",
    )

    def _inverse_custom_hours(self):
        """
        When custom hours is set, create overtime adjustment.
        Remove overtime if duration is negative.
        """
        for leave in self.filtered("enable_custom_hours"):
            duration = leave.custom_hours - leave.number_of_hours_display

            if duration > 0:
                if not leave.sudo().custom_overtime_id:
                    leave.sudo().custom_overtime_id = (
                        self.env["hr.attendance.overtime"]
                        .sudo()
                        .create(
                            {
                                "employee_id": leave.employee_id.sudo().id,
                                "date": leave.date_from,
                                "adjustment": True,
                                "duration": duration,
                            }
                        )
                    )
                else:
                    leave.sudo().custom_overtime_id.duration = duration
            elif duration <= 0 and leave.sudo().custom_overtime_id:
                leave.sudo().custom_overtime_id.unlink()

    def action_confirm(self):
        res = super().action_confirm()
        self._inverse_custom_hours()
        return res

    def action_draft(self):
        res = super().action_draft()
        self.sudo().custom_overtime_id.unlink()
        return res

    def unlink(self):
        self.sudo().custom_overtime_id.unlink()
        return super().unlink()
