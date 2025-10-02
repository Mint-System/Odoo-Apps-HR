import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrMissingBreak(models.Model):
    _name = "hr.missing.break"
    _description = "Missing Break"

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, ondelete='cascade', index=True)
    working_day = fields.Datetime(string="Date", default=fields.Datetime.now, required=True)

