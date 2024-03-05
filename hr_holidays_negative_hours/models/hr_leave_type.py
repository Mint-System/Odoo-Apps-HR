import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    compensate_overtime = fields.Boolean(
        "Compensate Extra Hours",
        default=False,
        help="Once a time off of this type is approved, the duration will be deducted from extra hours.",
    )
