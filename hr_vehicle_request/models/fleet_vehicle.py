from odoo import fields, models


class FleetVehicleInherit(models.Model):
    _inherit = "fleet.vehicle"

    reserved_ids = fields.One2many("fleet.reserved", "vehicle_id", readonly=1, ondelete="cascade")
