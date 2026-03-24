import logging

from odoo import models, fields
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import base64

_logger = logging.getLogger(__name__)


class HREmployee(models.Model):
    _inherit = "hr.employee"

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

            self.env['mail.mail'].create({
                'subject': f'Attendance Report {date_from:%Y-%m}',
                'body_html': '<p>Please find your attendance report attached.</p>',
                'email_to': emp.work_email,
                'attachment_ids': [(6, 0, [attachment.id])],
            }).send()