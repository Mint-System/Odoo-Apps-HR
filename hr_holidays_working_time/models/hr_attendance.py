import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    leave_id = fields.Many2one("hr.leave")
