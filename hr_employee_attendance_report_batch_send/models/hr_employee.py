import logging

from odoo import api, models, fields
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import base64

_logger = logging.getLogger(__name__)


class HREmployee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def _get_email_template(self):
        return self.env.ref(
            'hr_employee_attendance_report_batch_send.email_template_attendance_report', raise_if_not_found=True
        )

    def action_send_attendance_report_email(self):
        today = date.today()
        date_from = today + relativedelta(months=-1, day=1)
        date_until = today + relativedelta(day=1) - timedelta(days=1)

        for emp in self:
            if not emp.work_email:
                continue

            data = {
                'date_from': str(date_from),
                'date_until': str(date_until),
                'employee_id': emp.id,  # important!
            }

            report_model = self.env['ir.actions.report']

            pdf, _ = report_model._render_qweb_pdf(
                'hr_employee_attendance_report.hr_employee_report',
                res_ids=[emp.id],
                data={
                    'date_from': str(date_from),
                    'date_until': str(date_until),
                }
            )

            attachment_name = f'Attendance_Report_{emp.name}_{date_from.strftime("%B_%Y")}.pdf'

            attachment = self.env['ir.attachment'].create({
                'name': attachment_name,
                'type': 'binary',
                'datas': base64.b64encode(pdf),
                'mimetype': 'application/pdf',
            })

            mail_template = self._get_email_template()

            if mail_template:
                mail_template.with_context(
                    date_from=str(date_from),
                    date_until=str(date_until),
                ).send_mail(emp.id, email_values={
                    'attachment_ids': [(6, 0, [attachment.id])]
                }, force_send=True, email_layout_xmlid='mail.mail_notification_light')