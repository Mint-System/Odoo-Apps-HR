import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    enable_custom_hours = fields.Boolean(
        default=False,
        help="""When a time off of this type is created, the user can define a custom duration.
        The difference to the time-off hours is added as overtime hours.""",
    )
