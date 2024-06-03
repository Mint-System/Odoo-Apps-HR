import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = "hr.leave"

    leave_type_note = fields.Text(related='holiday_status_id.note', readonly=True)
