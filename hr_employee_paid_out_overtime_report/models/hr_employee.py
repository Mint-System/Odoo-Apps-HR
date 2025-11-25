from odoo import api, fields, models
from odoo.tools import float_round


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    total_overtime_paid_out = fields.Float(
        compute="_compute_total_overtime_paid_out",
        compute_sudo=True,
        groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance,hr.group_hr_user",
    )

    @api.depends("overtime_ids.duration", "attendance_ids")
    def _compute_total_overtime_paid_out(self):
        for employee in self:
            if employee.company_id.hr_attendance_overtime:
                employee.total_overtime_paid_out = float_round(
                    sum(
                        employee.overtime_ids.filtered(lambda o: o.paid_out).mapped(
                            "duration"
                        )
                    ),
                    2,
                )
            else:
                employee.total_overtime_paid_out = 0
