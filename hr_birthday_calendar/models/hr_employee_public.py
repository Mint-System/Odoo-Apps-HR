from odoo import fields, models, api
from datetime import datetime

class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    birthday_public = fields.Date('Birthday', compute='_compute_birthday_public', compute_sudo=True)

    def _compute_birthday_public(self):
        for employee in self:
            now = fields.Datetime.now()
            employee_id = self.sudo().env['hr.employee'].browse(employee.id)
            date = employee_id.birthday
            if date:
                now = now.replace(day=date.day,month=date.month)
            else:
                now = now.replace(year=1900)
            
            employee.birthday_public = now