# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Hr Employee Paid Out Overtime Report",
    "summary": """
        Shows List of employees with overtime to be paid out.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch",
    "category": "Repository",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance", "hr_employee_attendance_report"],
    "data": ["views/hr_attendance_overtime_views.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}