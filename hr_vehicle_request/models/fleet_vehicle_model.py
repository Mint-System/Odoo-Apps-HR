from odoo import fields, models


class FleetVehicleModel(models.Model):
    _inherit = "fleet.vehicle.model"

    vehicle_type = fields.Selection(
        selection_add=[("bus", "Bus"), ("cable_car", "Cable car")],
        ondelete={"bus": "set default", "cable_car": "set default"},
    )
