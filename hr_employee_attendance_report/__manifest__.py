{
    "name": "HR Employee Attendance Report",
    "summary": """
        Attendance and leave report.
    """,
    "author": "Mint System GmbH",
    "website": "https://github.com/OCA/sale-workflow",
    "category": "Human Resources",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance", "hr_holidays"],
    "data": [
        "report/hr_employee_report.xml",
        "report/res_users_report.xml",
        "security/ir.model.access.csv",
        "wizard/select_period.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
