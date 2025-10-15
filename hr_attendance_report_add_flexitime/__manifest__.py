# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Hr Attendance Report Add Flexitime",
    "summary": """
        Adds Flexitime to Attendance Report.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch",
    "category": "Repository",
    "version": "16.0.1.0.0",
    "post_init_hook": "post_init_hook",
    "license": "AGPL-3",
    "depends": ["base", "hr_attendance", "hr_holidays"],
    "data": [
     "security/ir.model.access.csv",
     "report/hr_attendance_report_views.xml",
     "data/planned_hours_cron.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}