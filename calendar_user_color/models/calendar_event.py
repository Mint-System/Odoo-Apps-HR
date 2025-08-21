from odoo import fields, models, api


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    # color = fields.Integer(compute="_compute_color")
    color = fields.Integer(related="user_id.color")
    
    # @api.depends("user_id")
    # def _compute_color(self):
    #     for event in self:
    #         event.color = event.user_id.color