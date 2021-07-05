from odoo import fields, models

class HrEmployee(models.Model):

    _inherit = "hr.employee"

    shortname = fields.Char(string="Shortname")
