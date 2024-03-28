{
    "name": "HR Attendance Policy",
    "summary": """
        Manage and check work time policies on attendance entries.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance_delta"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_attendance_policy.xml",
        "views/hr_employee.xml",
    ],
    "demo": ["data/hr_attendance_policy.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
