from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    total_paid_out_overtime = fields.Float(
        compute="_compute_total_paid_out_overtime",
        compute_sudo=True,
        groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance,hr.group_hr_user",
    )

    @api.depends("overtime_ids.duration", "attendance_ids")
    def _compute_total_paid_out_overtime(self):
        for employee in self:
            if employee.company_id.hr_attendance_overtime:
                employee.total_paid_out_overtime = round(
                    sum(employee.overtime_ids.filtered(lambda overtime: overtime.paid_out).mapped("duration")), 2
                )
            else:
                employee.total_paid_out_overtime = 0
