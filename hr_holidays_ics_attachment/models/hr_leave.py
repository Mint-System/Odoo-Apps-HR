import logging
import base64
from odoo import models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class HolidaysRequest(models.Model):
    _inherit = 'hr.leave'


    def _prepare_holidays_meeting_values(self):
        """BUGFIX: Set referernce on event"""
        res = super()._prepare_holidays_meeting_values()
        for i in res:
            res[i][0]['res_id'] = self.id
            res[i][0]['res_model_id'] = self.env['ir.model']._get(self._name).id            
        return res

    def action_approve(self):
        """OVERWRITE: odoo/addons/hr_holidays/models/hr_leave.py"""

        # if validation_type == 'both': this method is the first approval approval
        # if validation_type != 'both': this method calls action_validate() below
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Time off request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env.user.employee_id
        self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})
        
        self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
        if not self.env.context.get('leave_fast_create'):
            self.activity_update()

        # Post a second message, more verbose than the tracking message
        for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):

            # If calendar entry exists attach ics file to message
            if holiday.meeting_id:
                ics_file = holiday.meeting_id._get_ics_file().get(holiday.meeting_id.id)                  
                attachment = self.env['ir.attachment'].create({
                    'name': 'invitation.ics',
                    'mimetype': 'text/calendar',
                    'datas': base64.b64encode(ics_file)
                })

                holiday.message_post(
                    body=_(
                        'Your %(leave_type)s planned on %(date)s has been accepted',
                        leave_type=holiday.holiday_status_id.display_name,
                        date=holiday.date_from
                    ),
                    partner_ids=holiday.employee_id.user_id.partner_id.ids,
                    attachment_ids=[attachment.id]
                )
            else:
                holiday.message_post(
                    body=_(
                        'Your %(leave_type)s planned on %(date)s has been accepted',
                        leave_type=holiday.holiday_status_id.display_name,
                        date=holiday.date_from
                    ),
                    partner_ids=holiday.employee_id.user_id.partner_id.ids
                )        
        
        return True