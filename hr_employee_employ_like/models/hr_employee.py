from odoo import fields, models

class HrEmployee(models.Model):

    _inherit = "hr.employee"

    employ_like_id = fields.Many2one('hr.employee', string='Employ like')
