# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "HR Employee Attendance Report Automation",
    "summary": """
        Automated monthly generation and sending of attendance reports.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch",
    "category": "Human Resources",
    "development_status": "Production/Stable",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_employee_attendance_report", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee_report_automation_views.xml",
        "data/cron_data.xml",
        "data/mail_template_data.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
