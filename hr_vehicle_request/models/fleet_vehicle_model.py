from odoo import _, api, fields, models
from odoo.exceptions import Warning


class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'
    
    vehicle_type = fields.Selection(selection_add=[
        ('bus', 'Bus'),
        ('cable_car', 'Cable car')],
        ondelete={
            "bus": "set default",
            "cable_car": "set default"
        },)
