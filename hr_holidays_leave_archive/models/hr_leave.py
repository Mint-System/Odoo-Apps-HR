import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    active = fields.Boolean(default=True)

    def toggle_active(self):
        res = super(HolidaysRequest, self).toggle_active()
        # self.state = 'cancel'
        return res
