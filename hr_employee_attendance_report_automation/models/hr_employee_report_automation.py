import logging
from datetime import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrEmployeeReportAutomation(models.Model):
    _name = "hr.employee.report.automation"
    _description = "HR Employee Attendance Report Automation"

    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    employee_ids = fields.Many2many(
        "hr.employee",
        string="Employees",
        help="Employees to include in the report. If empty, all employees will be included.",
    )
    recipient_ids = fields.Many2many(
        "res.partner",
        string="Recipients",
        help="Recipients who will receive the report by email.",
    )
    mail_template_id = fields.Many2one(
        "mail.template",
        string="Email Template",
        domain=[("model", "=", "hr.employee.report.automation")],
        help="Email template used to send the report.",
    )
    last_run = fields.Datetime(string="Last Run", readonly=True)
    last_period_start = fields.Date(string="Last Period Start", readonly=True)
    last_period_end = fields.Date(string="Last Period End", readonly=True)

    def action_generate_and_send_reports(self):
        """Generate attendance reports for last month and send them via email."""
        self.ensure_one()

        # Calculate last month's period
        today = fields.Date.context_today(self)
        period_start = today.replace(day=1) - fields.relativedelta(months=1)
        period_end = today.replace(day=1) - fields.relativedelta(days=1)

        # Get employees
        employees = self.employee_ids if self.employee_ids else self.env["hr.employee"].search(
            [("company_id", "=", self.company_id.id)]
        )

        if not employees:
            _logger.warning("No employees found for automation %s", self.name)
            return {"type": "ir.actions.client", "tag": "display_notification", "params": {
                "title": "Report Generation",
                "message": "No employees found to generate reports for.",
                "type": "warning",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            }}

        # Generate PDF report for each employee
        report_action = self.env.ref("hr_employee_attendance_report.hr_employee_report")
        report_data = {
            "date_from": period_start.strftime("%Y-%m-%d"),
            "date_until": period_end.strftime("%Y-%m-%d"),
        }

        for employee in employees:
            try:
                # Generate PDF
                pdf_content, _ = report_action._render_qweb_pdf(
                    res_ids=[employee.id],
                    data=report_data,
                )

                # Create attachment
                attachment_name = f"Attendance_Report_{employee.name}_{period_start.strftime('%Y_%m')}.pdf"
                attachment = self.env["ir.attachment"].create(
                    {
                        "name": attachment_name,
                        "type": "binary",
                        "datas": pdf_content.decode("base64"),
                        "res_model": "hr.employee",
                        "res_id": employee.id,
                    }
                )

                # Send email if recipients are defined
                if self.recipient_ids and self.mail_template_id:
                    self._send_email(employee, attachment, period_start, period_end)

            except Exception as e:
                _logger.error(
                    "Error generating report for employee %s: %s",
                    employee.name,
                    e,
                    exc_info=True,
                )

        # Update last run info
        self.write(
            {
                "last_run": fields.Datetime.now(),
                "last_period_start": period_start,
                "last_period_end": period_end,
            }
        )

        return {"type": "ir.actions.client", "tag": "display_notification", "params": {
            "title": "Report Generation",
            "message": f"Reports generated successfully for {len(employees)} employee(s).",
            "type": "success",
            "sticky": False,
            "next": {"type": "ir.actions.act_window_close"},
        }}

    def _send_email(self, employee, attachment, period_start, period_end):
        """Send email with the attendance report attachment."""
        self.ensure_one()

        # Prepare email values
        email_values = {
            "email_to": ",".join(self.recipient_ids.mapped("email")),
            "attachment_ids": [(6, 0, [attachment.id])],
        }

        # Send email using the template
        self.mail_template_id.send_mail(
            self.id,
            force_send=True,
            email_values=email_values,
        )

        _logger.info(
            "Sent attendance report for employee %s to %s",
            employee.name,
            self.recipient_ids.mapped("email"),
        )

    def action_test_run(self):
        """Test run the automation without updating last_run field."""
        self.ensure_one()

        # Store original last_run to restore after test
        original_last_run = self.last_run

        # Call the main method
        result = self.action_generate_and_send_reports()

        # Restore original last_run
        self.last_run = original_last_run

        return result
