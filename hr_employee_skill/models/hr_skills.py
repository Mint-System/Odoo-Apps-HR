from odoo import fields, models


class EmployeeSkill(models.Model):
    _inherit = "hr.employee.skill"

    level_progress = fields.Integer(
        related="skill_level_id.level_progress", store=True, group_operator="avg"
    )
