from odoo import _, api, fields, models
from odoo.exceptions import Warning


class EmployeeFleet(models.Model):
    _name = "employee.fleet"
    _description = "Employee Vehicle Request"
    _inherit = "mail.thread"

    name = fields.Char(string="Request Number", copy=False)
    employee = fields.Many2one(
        "hr.employee",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env.user.employee_id,
    )
    req_date = fields.Date(
        string="Requested Date",
        default=fields.Date.context_today,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Requested Date",
    )
    available_vehicle_ids = fields.Many2many(
        "fleet.vehicle",
        string="Available Vehicles",
        compute="_compute_available_vehicle_ids",
    )
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        required=True,
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)]},
    )
    vehicle_type = fields.Selection(related='vehicle_id.model_id.vehicle_type')
    date_from = fields.Datetime(
        string="From",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_to = fields.Datetime(
        string="To", required=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    reserved_id = fields.Many2one("fleet.reserved", copy=False)
    returned_date = fields.Datetime(readonly=1)
    purpose = fields.Text(
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Purpose",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("waiting", "Waiting for Approval"),
            ("cancel", "Cancel"),
            ("confirm", "Approved"),
            ("reject", "Rejected"),
            ("return", "Returned"),
        ],
        default="draft",
    )

    @api.constrains("date_from", "date_to")
    def onchange_date_to(self):
        for reservation in self:
            if reservation.date_from > reservation.date_to:
                raise Warning(_("Date To must be greater than Date From."))

    def unlink(self):
        if self.reserved_id:
            self.reserved_id.unlink()
        return super().unlink()

    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].next_by_code("employee.fleet")
        return super(EmployeeFleet, self).create(vals)

    @api.depends('date_from', 'date_to')
    def _compute_available_vehicle_ids(self):
        """Return list of available vehicles."""
        for request in self:
            if request.date_from and request.date_to:

                # Get all vehicles
                available_vehicle_ids = self.env['fleet.vehicle'].search([])
                for vehicle in available_vehicle_ids:
                    for reservation in vehicle.reserved_ids:

                        if reservation.date_from <= self.date_from <= reservation.date_to:
                            available_vehicle_ids = available_vehicle_ids - vehicle

                        elif self.date_from < reservation.date_from:

                            if reservation.date_from <= self.date_to <= reservation.date_to:
                                available_vehicle_ids = available_vehicle_ids - vehicle

                            elif self.date_to > reservation.date_to:
                                available_vehicle_ids = available_vehicle_ids - vehicle

                self.available_vehicle_ids = available_vehicle_ids
            else:
                self.available_vehicle_ids = []

    def send(self):
        if not (self.vehicle_id in self.available_vehicle_ids):
            raise Warning(
                _("Sorry this vehicle is already requested by another employee.")
            )
        else:
            reserved_id = self.vehicle_id.reserved_ids.sudo().create(
                {
                    "employee": self.employee.id,
                    "date_from": self.date_from,
                    "date_to": self.date_to,
                    "vehicle_id": self.vehicle_id.id,
                }
            )
            self.write({"reserved_id": reserved_id.id})
            self.state = "waiting"
            self.message_post(
                subject=_("%s: Validation") % self.name,
                body=_(
                    "Hi %s,<br>You have received the vehicle request %s for validation."
                )
                % (self.vehicle_id.manager_id.name, self.name),
                partner_ids=[self.vehicle_id.manager_id.partner_id.id],
            )

    def approve(self):
        self.state = "confirm"
        self.message_post(
            subject=_("%s: Approved") % self.name,
            body=_("Hi %s,<br>Your vehicle request for the reference %s is approved.")
            % (self.employee.name, self.name),
            partner_ids=[self.employee.user_partner_id.id],
        )

    def reject(self):
        if self.reserved_id:
            self.reserved_id.unlink()
        self.state = "reject"
        self.message_post(
            subject=_("%s: Rejected") % self.name,
            body=_(
                "Hi %s,<br>Sorry, Your vehicle request for the reference %s is rejected."
            )
            % (self.employee.name, self.name),
            partner_ids=[self.employee.user_partner_id.id],
        )

    def cancel(self):
        """Employee can cancel a request."""
        if self.reserved_id:
            self.reserved_id.sudo().unlink()
        self.state = "cancel"

    def draft(self):
        self.state = "draft"

    def returned(self):
        """Employee can return a vehicle."""
        if self.reserved_id:
            self.reserved_id.sudo().unlink()
        self.returned_date = fields.datetime.now()
        self.state = "return"
