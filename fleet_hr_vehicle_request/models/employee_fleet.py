from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class EmployeeFleet(models.Model):
    _inherit = 'employee.fleet'

    state = fields.Selection(tracking=True)
    odometer = fields.Float(string='Last Odometer Value', copy=False)
    private_usage = fields.Boolean()

    def returned(self):
        if not self.odometer:
            raise Warning(_('Odometer value cannot be null.'))
        super().returned()
        self.env['fleet.vehicle.assignation.log'].sudo().create({
            'date_start': self.date_from,
            'date_end': self.date_to,
            'vehicle_id': self.fleet.id,
            'driver_id': self.employee.user_partner_id.id 
        })
        if self.odometer:
            self.env['fleet.vehicle.odometer'].sudo().create({
                'date': self.returned_date,
                'value': self.odometer,
                'vehicle_id': self.fleet.id,
                'driver_id': self.employee.user_partner_id.id 
            })