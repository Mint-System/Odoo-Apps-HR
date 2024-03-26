from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class Employee(models.Model):
    _inherit = 'hr.employee'

    policy_ids = fields.Many2many('hr.attendance.policy', string='Policies', compute='_compute_policies')

    @api.model
    def action_create_attendance_policy(self):
        action = self.env.ref('hr_attendance_policy.hr_attendance_policy_action').read()[0]
        action['views'] = [(self.env.ref('hr_attendance_policy.view_hr_attendance_policy_form').id, 'form')]
        action['context'] = {'form_view_initial_mode': 'edit'}
        return action

    @api.depends('department_id', 'job_id')
    def _compute_policies(self):
        for employee in self:
            _logger.info('Computing policies for employee %s with department_id %s and job_id %s', employee.name, employee.department_id.id, employee.job_id.id)
            policies = self.env['hr.attendance.policy'].search([
                ('department_id', '=', employee.department_id.id),
                ('job_id', '=', employee.job_id.id)
            ])
            employee.policy_ids = [(6, 0, policies.ids)]
