import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    record_as_attendance = fields.Boolean(
        "Record as Attendance",
        help="If leave is confirmed an attendance will be created.",
    )
    calendar_id = fields.Many2one(
        "resource.calendar",
        help="Select a calendar for the attendance time calculation. If empty, the calendar of the employee will be used.",
    )
    max_leave_hours = fields.Integer(
        help="The maximum leave hours for which attendances will be created. Set to 0 for no limit."
    )

    @api.constrains()
    def _check_time_type(self):
        if self.record_as_attendance and self.time_type != "other":
            raise ValidationError(
                "Record as attendance can only be used with other time type."
            )
