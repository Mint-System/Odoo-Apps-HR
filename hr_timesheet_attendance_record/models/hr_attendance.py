from datetime import timedelta

from odoo import api, fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    timesheet_ids = fields.One2many(
        "account.analytic.line",
        "attendance_id",
        string="Timesheets",
    )
    timesheet_count = fields.Integer(
        compute="_compute_timesheet_count",
        string="Timesheet Count",
    )
    check_out = fields.Datetime(
        compute="_compute_check_out",
        store=True,
        readonly=False,
    )

    @api.depends("timesheet_ids.unit_amount")
    def _compute_check_out(self):
        for attendance in self:
            if attendance.check_in:
                total_hours = sum(attendance.timesheet_ids.mapped("unit_amount"))
                attendance.check_out = attendance.check_in + timedelta(hours=total_hours)

    @api.depends("timesheet_ids")
    def _compute_timesheet_count(self):
        for attendance in self:
            attendance.timesheet_count = len(attendance.timesheet_ids)

    def action_view_timesheet_ids(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Timesheets",
            "res_model": "account.analytic.line",
            "view_mode": "list,form",
            "domain": [("attendance_id", "=", self.id)],
        }
