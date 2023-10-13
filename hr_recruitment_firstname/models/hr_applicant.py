import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Applicant(models.Model):
    _inherit = "hr.applicant"

    firstname = fields.Char("First name", index=True)
    lastname = fields.Char("Last name", index=True)
    partner_name = fields.Char("Applicant's Name", compute="_compute_name")

    @api.depends("firstname", "lastname")
    def _compute_name(self):
        for record in self:
            record.partner_name = self.env["res.partner"]._get_computed_name(
                record.lastname, record.firstname
            )

    def website_form_input_filter(self, request, values):
        if "firstname" in values and "lastname" in values:
            values.setdefault(
                "name",
                "%s %s's Application" % (values["firstname"], values["lastname"]),
            )
        return values
