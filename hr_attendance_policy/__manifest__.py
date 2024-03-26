{
    "name": "Hr Attendance Policy",
    "summary": """
        HR Attendance Policy.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_attendance_policy.xml",
        "views/hr_employee.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    }
