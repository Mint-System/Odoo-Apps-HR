from odoo import _, api, fields, models
from odoo.exceptions import Warning


class FleetVehicleInherit(models.Model):
    _inherit = "fleet.vehicle"

    reserved_ids = fields.One2many(
        "fleet.reserved", "vehicle_id", readonly=1, ondelete="cascade"
    )
