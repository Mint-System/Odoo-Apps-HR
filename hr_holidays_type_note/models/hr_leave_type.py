import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    note = fields.Text()
