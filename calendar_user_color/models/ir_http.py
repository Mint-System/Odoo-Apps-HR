# -*- coding: utf-8 -*-

from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'


    def session_info(self):
        info = super().session_info()
        info['color'] = self.env.user.color
        return info