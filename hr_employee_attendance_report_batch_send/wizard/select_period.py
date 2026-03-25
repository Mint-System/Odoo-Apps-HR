import logging
import base64

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HREmployeeAttendanceReportSelectPeriod(models.TransientModel):
    _inherit = "hr_employee_attendance_report.select_period"


    @api.model
    def _get_email_template(self):
        return self.env.ref(
            'hr_employee_attendance_report_batch_send.email_template_attendance_report', raise_if_not_found=True
        )

    def action_send_attendance_report_email(self):
        self.ensure_one()

        # today = date.today()
        # date_from = today + relativedelta(months=-1, day=1)
        # date_until = today + relativedelta(day=1) - timedelta(days=1)

        employees = self.env['hr.employee'].browse(
            self.env.context.get('active_ids', [])
        )

        for emp in employees:
            if not emp.work_email:
                continue

            data = {
                'date_from': str(self.date_from),
                'date_until': str(self.date_until),
            }

            report_model = self.env['ir.actions.report']

            pdf, _ = report_model._render_qweb_pdf(
                'hr_employee_attendance_report.hr_employee_report',
                res_ids=[emp.id],
                data=data
            )

            attachment_name = f'Attendance_Report_{emp.name}_{self.date_from.strftime("%Y%m%d")}-{self.date_until.strftime("%Y%m%d")}.pdf'

            attachment = self.env['ir.attachment'].create({
                'name': attachment_name,
                'type': 'binary',
                'datas': base64.b64encode(pdf),
                'mimetype': 'application/pdf',
                'res_model': 'hr.employee',
                'res_id': emp.id,  
            })

            if attachment:
                emp.message_post(
                    body="Attendance report generated and sent by email.",
                    attachment_ids=[attachment.id]
                )

            mail_template = self._get_email_template()

            if mail_template:
                mail_template.with_context(
                    date_from=str(self.date_from),
                    date_until=str(self.date_until),
                ).send_mail(emp.id, email_values={
                    'attachment_ids': [(6, 0, [attachment.id])]
                }, force_send=True, email_layout_xmlid='mail.mail_notification_light')