from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    shortname = fields.Char(readonly=True)
