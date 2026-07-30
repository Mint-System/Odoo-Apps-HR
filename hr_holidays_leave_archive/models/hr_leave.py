import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    active = fields.Boolean(default=True, readonly=False)


    def toggle_active(self):
        """Allow native archive/unarchive by injecting the bypass context."""
        return super(HolidaysRequest, self.with_context(from_cancel_wizard=True)).toggle_active()

    

