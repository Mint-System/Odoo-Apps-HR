import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    ignore_missing_attendance = fields.Boolean(
        default=False,
        help="""When checked leaves of this type will be ignored in the missing attendance check.""",
    )
