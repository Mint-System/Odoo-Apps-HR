import logging
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HRAttendanceMissingSelectPeriod(models.TransientModel):

    _name = "hr_attendance_missing.select_period"
    _description = "Attendance Missing Select Period"

    date_from = fields.Date(
        string="From",
        required=True,
        default=lambda *a: str(date.today() + relativedelta(days=-1)),
    )
    date_to = fields.Date(
        string="Until",
        required=True,
        default=lambda *a: str(date.today() + relativedelta(days=-1)),
    )

    def action_create_missing_attendances(self):
        active_ids = self.env.context["active_ids"]
        employees = self.env["hr.employee"].browse(active_ids)
        return employees._create_missing_attendances(
            date_from=self.date_from, date_to=self.date_to
        )