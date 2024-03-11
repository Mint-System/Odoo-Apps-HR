from odoo import models, fields, api

class HRAttendancePolicy(models.Model):
    _name = 'hr.attendance.policy'
    _description = 'Attendance Policy'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', required=True)
    rule_ids = fields.One2many('hr.attendance.rule', 'policy_id', string='Rules')
    warning_message = fields.Text('Warning Message')

class HRAttendanceRule(models.Model):
    _name = 'hr.attendance.rule'
    _description = 'Attendance Rule'

    min_work_hours = fields.Float('Minimum Work Hours')
    max_work_hours = fields.Float('Maximum Work Hours')
    min_delta = fields.Float('Minimum Delta')
    period_days = fields.Integer('Period Days')
    policy_id = fields.Many2one('hr.attendance.policy', string='Policy')
    day_of_week = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ], 'Day of the Week', required=True)
