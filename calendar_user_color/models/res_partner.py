from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_color(self):
        return self.color

