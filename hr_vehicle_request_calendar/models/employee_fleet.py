import base64

from odoo import _, fields, models


class EmployeeFleet(models.Model):
    _inherit = "employee.fleet"

    meeting_id = fields.Many2one("calendar.event", string="Meeting", readonly=True, copy=False)

    def _prepare_meeting_values(self):
        self.ensure_one()
        meeting_values = {
            "name": _("Vehicle Reservation %s") % self.name,
            "description": self.purpose,
            "start": self.date_from,
            "stop": self.date_to,
            "partner_ids": [(4, self.employee.user_partner_id.id)],
            "user_id": self.employee.user_id.id,
            "privacy": "confidential",
            "show_as": "busy",
        }
        return meeting_values

    def approve(self):
        """#OVERWRITE Approve method."""
        self.ensure_one()
        self.state = "confirm"

        # Generate meeting
        self.meeting_id = self.env["calendar.event"].create(
            self._prepare_meeting_values()
        )

        # Get ics file and create attachment
        ics_file = self.meeting_id._get_ics_file().get(self.meeting_id.id)
        attachment = self.env["ir.attachment"].create(
            {
                "name": "invitation.ics",
                "mimetype": "text/calendar",
                "datas": base64.b64encode(ics_file),
            }
        )

        # Send message with attachment
        self.message_post(
            subject=_("%s: Approved") % self.name,
            body=_("Hi %s,<br>Your vehicle request for the reference %s is approved.")
            % (self.employee.name, self.name),
            partner_ids=[self.employee.user_partner_id.id],
            attachment_ids=[attachment.id],
        )

    def reject(self):
        self.meeting_id.unlink()
        return super().reject()

    def cancel(self):
        self.meeting_id.unlink()
        return super().cancel()

    def unlink(self):
        self.meeting_id.unlink()
        return super().unlink()
