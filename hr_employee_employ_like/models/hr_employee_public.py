from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    employ_like_id = fields.Many2one("hr.employee", string="Employ like")
