import base64
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class HREmployeeAttendanceReportSelectPeriod(models.TransientModel):
    _inherit = "hr_employee_attendance_report.select_period"

    @api.model
    def _get_email_template(self):
        return self.env.ref(
            "hr_employee_attendance_report_batch_send.email_template_attendance_report", raise_if_not_found=True
        )

    def action_send_attendance_report_email(self):
        self.ensure_one()

        employees = self.env["hr.employee"].browse(self.env.context.get("active_ids", []))

        for emp in employees:
            if not emp.work_email:
                continue

            data = {
                "date_from": str(self.date_from),
                "date_until": str(self.date_until),
            }

            report_model = self.env["ir.actions.report"]

            pdf, _ = report_model._render_qweb_pdf(
                "hr_employee_attendance_report.hr_employee_report", res_ids=[emp.id], data=data
            )

            attachment_name = f'Attendance_Report_{emp.name}_{self.date_from.strftime("%Y%m%d")}-{self.date_until.strftime("%Y%m%d")}.pdf'

            attachment = self.env["ir.attachment"].create(
                {
                    "name": attachment_name,
                    "type": "binary",
                    "datas": base64.b64encode(pdf),
                    "mimetype": "application/pdf",
                    "res_model": "hr.employee",
                    "res_id": emp.id,
                }
            )

            template = self._get_email_template()

            if template:
                template = template.with_context(
                    date_from=str(self.date_from),
                    date_until=str(self.date_until),
                )
                values = {
                    "subject": template._render_field("subject", [emp.id])[emp.id],
                    "body_html": template._render_field("body_html", [emp.id])[emp.id],
                    "email_from": template._render_field("email_from", [emp.id])[emp.id],
                    "email_to": template._render_field("email_to", [emp.id])[emp.id] or emp.work_email,
                    "attachment_ids": [(4, attachment.id)],
                }

                mail = self.env["mail.mail"].create(values).send()

            if attachment:
                body = "Attendance report generated"
            if mail:
                body += " and sent by email"
            emp.message_post(body=body, attachment_ids=[attachment.id])
