from odoo import fields, models


class Contacts(models.Model):
    _inherit = "calendar.filters"

    partner_color = fields.Integer(related="partner_id.color", store=True, readonly=True, default=5)
