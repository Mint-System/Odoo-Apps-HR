import logging
from odoo import fields, models, api, _
_logger = logging.getLogger(__name__)


class Hr Attendance Missing(models.Model):
    _name = 'hr_attendance_missing.document'
    _description = 'Hr Attendance Missing Document'

    name = fields.Char()
    value = fields.Integer()