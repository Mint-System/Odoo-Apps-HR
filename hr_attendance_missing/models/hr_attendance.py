import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    is_missing_attendance = fields.Boolean()
