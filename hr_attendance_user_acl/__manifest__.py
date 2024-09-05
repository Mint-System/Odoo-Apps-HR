{
    "name": "HR Attendance User Acl",
    "summary": """
          Allow attendance users to create and edit their attendance entries.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance_calendar_view"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_attendance.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
