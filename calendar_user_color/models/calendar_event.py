from odoo import fields, models, api


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    color = fields.Integer(related="user_id.color")