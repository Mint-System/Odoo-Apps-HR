import logging
import base64
from odoo import models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class HolidaysRequest(models.Model):
    _inherit = 'hr.leave'

    def action_approve(self):
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
            # Get ics file and create attachment
            ics_file = holiday.meeting_id._get_ics_file().get(holiday.meeting_id.id)
            attachment = self.env['ir.attachment'].create({
                'name': 'invitation.ics',
                'mimetype': 'text/calendar',
                'datas': base64.b64encode(ics_file)
            })
            
            holiday.message_post(
                body=_('Your %s planned on %s has been accepted') % (holiday.holiday_status_id.display_name, holiday.date_from),
                partner_ids=holiday.employee_id.user_id.partner_id.ids,
                attachment_ids=[attachment.id])
        
        return True