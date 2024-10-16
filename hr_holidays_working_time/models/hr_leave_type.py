import logging

from odoo import _, api, fields, models
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
        help="""Select a calendar for the attendance time calculation.
            If empty, the calendar of the employee will be used.""",
    )
    calendar_max_hours = fields.Integer(
        default=0,
        help="""If leave hours is greater than this value, the employee calendar will be used. Set to 0 to disable.""",
    )

    @api.constrains()
    def _check_time_type(self):
        if self.record_as_attendance and self.time_type != "other":
            raise ValidationError(
                _("Record as attendance can only be used with other time type.")
            )
