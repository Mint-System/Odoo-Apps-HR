from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    color_hex = fields.Char(string='Color (Hex)')


    @api.onchange('color_hex')
    def onchange_color_hex(self):
        if self.color_hex:
            # convert hexadecimal color code to integer color index
            # you can use a library like colorsys or matplotlib.colors to do this
            # for simplicity, let's assume we're using a simple conversion
            color_index = int(self.color_hex.lstrip('#'), 16)
            self.color = color_index