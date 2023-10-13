from odoo import _, api, fields, models
from odoo.exceptions import Warning


class EmployeeFleet(models.Model):
    _inherit = "employee.fleet"

    trip = fields.Float(
        copy=False, readonly=True, states={"confirm": [("readonly", False)]}
    )
    state = fields.Selection(tracking=True)
    odometer = fields.Float(
        string="Last Odometer Value",
        copy=False,
        readonly=True,
        states={"confirm": [("readonly", False)]},
    )
    private_usage = fields.Boolean(
        readonly=True, states={"draft": [("readonly", False)]}
    )

    def returned(self):
        if not self.odometer:
            raise Warning(_("Odometer value cannot be null."))
        super().returned()
        self.env["fleet.vehicle.assignation.log"].sudo().create(
            {
                "date_start": self.date_from,
                "date_end": self.date_to,
                "vehicle_id": self.fleet.id,
                "driver_id": self.employee.user_partner_id.id,
            }
        )
        if self.odometer:
            self.env["fleet.vehicle.odometer"].sudo().create(
                {
                    "date": self.returned_date,
                    "value": self.odometer,
                    "vehicle_id": self.fleet.id,
                    "driver_id": self.employee.user_partner_id.id,
                    "request_id": self.id,
                }
            )

    @api.onchange("odometer")
    def _onchange_trip(self):
        """Calculate distance by substracting current odometer value from last."""
        last_odometer = self.env["fleet.vehicle.odometer"].search(
            [("vehicle_id", "=", self.fleet.id)], order="value desc", limit=1
        )
        if last_odometer:
            self.trip = self.odometer - last_odometer.value


class FleetVehicleOdometer(models.Model):
    _inherit = "fleet.vehicle.odometer"

    request_id = fields.Many2one("employee.fleet")
