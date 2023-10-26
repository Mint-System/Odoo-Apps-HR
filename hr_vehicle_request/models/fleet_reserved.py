from odoo import _, api, fields, models
from odoo.exceptions import Warning


class FleetReservedTime(models.Model):
    _name = "fleet.reserved"
    _description = "Reserved Time"

    employee = fields.Many2one("hr.employee", required=True)
    date_from = fields.Datetime(string="Reserved Date From", required=True)
    date_to = fields.Datetime(string="Reserved Date To", required=True)
    vehicle_id = fields.Many2one("fleet.vehicle", required=True)

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, rec.vehicle_id.display_name))
        return res
