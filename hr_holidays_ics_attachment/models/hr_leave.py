import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    def _prepare_holidays_meeting_values(self):
        """BUGFIX: Set referernce on event"""
        res = super()._prepare_holidays_meeting_values()
        for i in res:
            res[i][0]["res_id"] = self.id
            res[i][0]["res_model_id"] = self.env["ir.model"]._get(self._name).id
        return res

    # remove messaging from approve
    def action_approve(self):
        if any(holiday.state != "confirm" for holiday in self):
            raise UserError(_('Time off request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env.user.employee_id
        self.filtered(lambda hol: hol.validation_type == "both").write(
            {"state": "validate1", "first_approver_id": current_employee.id}
        )

        # Let standard validation + calendar creation happen here
        self.filtered(lambda hol: hol.validation_type != "both").action_validate()

        if not self.env.context.get("leave_fast_create"):
            self.activity_update()

        return True

    # add messaging to validate action
    def action_validate(self):
        res = super().action_validate()

        # At this point _validate_leave_request() has already created
        # the calendar.event and written meeting_id (for holiday_type='employee').
        for holiday in self.filtered(lambda h: h.employee_id.user_id):
            attachments = []

            # Safety check: _create_calendar_meeting only runs for holiday_type='employee'
            if holiday.meeting_id:
                ics_data = holiday.meeting_id._get_ics_file().get(holiday.meeting_id.id)
                if ics_data:
                    attachments = [("invitation.ics", ics_data)]

            holiday.message_post(
                body=_(
                    "Your %(leave_type)s planned on %(date)s has been accepted",
                    leave_type=holiday.holiday_status_id.display_name,
                    date=holiday.date_from,
                ),
                partner_ids=holiday.employee_id.user_id.partner_id.ids,
                attachments=attachments,
                subtype_xmlid="mail.mt_comment",  # public comment → e-mail is sent
            )

        return res
