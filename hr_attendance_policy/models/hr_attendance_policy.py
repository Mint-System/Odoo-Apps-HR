from odoo import models, fields, api

class HRAttendancePolicy(models.Model):
    _name = 'hr.attendance.policy'
    _description = 'Attendance Policy'

    active = fields.Boolean('Active', default=True, help="Indicates if the policy is active.")
    name = fields.Char('Name', required=True, help="The name of the attendance policy.")
    rule_ids = fields.One2many('hr.attendance.rule', 'policy_id', string='Rules', help="The set of rules that define this policy.")
    warning_message = fields.Text('Warning Message', help="A message to display if the policy is violated.")
    department_id = fields.Many2one('hr.department', string='Department', help="The department this policy applies to. Used to automatically apply policies to employees based on their department.")
    job_id = fields.Many2one('hr.job', string='Job Position', help="The job position this policy applies to. Used to automatically apply policies to employees based on their job position.")

    @api.model
    def action_create_attendance_policy(self):
        return {
            'name': 'Create Attendance Policy',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.attendance.policy',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'form_view_initial_mode': 'edit'},
            'target': 'current',
        }

class HRAttendanceRule(models.Model):
    _name = 'hr.attendance.rule'
    _description = 'Attendance Rule'

    policy_id = fields.Many2one('hr.attendance.policy', string='Policy', required=True, ondelete='cascade', index=True, help="The attendance policy this rule belongs to.")
    min_work_hours = fields.Float('Minimum Work Hours', help="The minimum number of work hours required by this rule.")
    max_work_hours = fields.Float('Maximum Work Hours', help="The maximum number of work hours allowed by this rule.")
    min_delta = fields.Float('Minimum Delta', help="The minimum acceptable difference in work hours.")
    period_days = fields.Integer('Period Days', help="The number of days over which to apply this rule.")
    day_of_week = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ], 'Day of the Week', required=True, help="The specific day of the week to which this rule applies.")
