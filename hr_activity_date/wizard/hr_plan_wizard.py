from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class HrPlanWizard(models.TransientModel):
    _inherit = 'hr.plan.wizard'

    def _prepare_activity_values(self, activity_type, responsible, date_deadline=False):
        """Hook to insert values"""
        return {
            'res_id': self.employee_id.id,
            'res_model_id': self.env['ir.model']._get('hr.employee').id,
            'summary': activity_type.summary,
            'note': activity_type.note,
            'activity_type_id': activity_type.activity_type_id.id,
            'user_id': responsible.id,
            'date_deadline': date_deadline,
        }

    def action_launch(self):
        """OVERWRITE set date deadline"""
        contract_id =  self.employee_id.contract_id

        if not contract_id:
            raise UserError(_('This user does not have an active contract.'))

        for activity_type in self.plan_id.plan_activity_type_ids:
            responsible = activity_type.get_responsible_id(self.employee_id)

            if self.env['hr.employee'].with_user(responsible).check_access_rights('read', raise_exception=False):
                
                date_deadline = self.env['mail.activity']._calculate_date_deadline(activity_type.activity_type_id)
                
                # Overwrite date deadline with contract date
                if activity_type.activity_date_input == 'start' and contract_id.date_start:
                    date_deadline = contract_id.date_start
                if activity_type.activity_date_input == 'end' and contract_id.date_end:
                    date_deadline = contract_id.date_end
    
                # Apply offset
                if activity_type.activity_date_offset_days != 0:
                    date_deadline = date_deadline + timedelta(days=activity_type.activity_date_offset_days)

                values = self._prepare_activity_values(activity_type, responsible, date_deadline)
                self.env['mail.activity'].create(values)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'res_id': self.employee_id.id,
            'name': self.employee_id.display_name,
            'view_mode': 'form',
            'views': [(False, "form")],
        }
