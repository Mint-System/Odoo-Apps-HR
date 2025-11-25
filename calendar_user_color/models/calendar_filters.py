from odoo import fields, models


class CalendarFilter(models.Model):
    _inherit = "calendar.filters"

    partner_color = fields.Integer(
        related="partner_id.color",
        readonly=True,
    )
