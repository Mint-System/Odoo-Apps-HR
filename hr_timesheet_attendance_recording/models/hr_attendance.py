# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, time, timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    timesheet_ids = fields.One2many(
        "account.analytic.line",
        "attendance_id",
        string="Timesheets",
    )
    timesheet_count = fields.Integer(
        compute="_compute_timesheet_count",
    )
    check_out = fields.Datetime(
        compute="_compute_check_out",
        store=True,
    )

    @api.depends("timesheet_ids")
    def _compute_timesheet_count(self):
        for attendance in self:
            attendance.timesheet_count = len(attendance.timesheet_ids)

    @api.depends("timesheet_ids", "timesheet_ids.unit_amount", "check_in")
    def _compute_check_out(self):
        for attendance in self:
            if attendance.timesheet_ids:
                total_hours = sum(attendance.timesheet_ids.mapped("unit_amount"))
                attendance.check_out = attendance.check_in + timedelta(
                    hours=total_hours
                )
            else:
                attendance.check_out = False

    def action_view_timesheets(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Timesheets",
            "res_model": "account.analytic.line",
            "view_mode": "list,form",
            "domain": [("attendance_id", "=", self.id)],
        }
