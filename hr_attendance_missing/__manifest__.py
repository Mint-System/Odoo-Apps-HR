{
    "name": "HR Attendance Missing",
    "summary": """
        Create attendance entries on working days without leave.
    """,
    "author": "Mint System GmbH",
    "website": "https://github.com/OCA/sale-workflow",
    "category": "Human Resources",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "wizard/select_period.xml",
        "views/hr_attendance_views.xml",
        "views/hr_leave_type_views.xml",
    ],
    "depends": ["hr_attendance", "hr_holidays"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
