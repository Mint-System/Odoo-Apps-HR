# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Hr Attendance Report Pivot Add Leaves",
    "summary": """
        Adds leaves to Attendance Pivot Report.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch",
    "category": "Repository",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base", "hr_attendance", "hr_holidays"],
    "data": [
      "security/ir.model.access.csv",
      "views/hr_attendance_leave_report_views.xml",
      "views/hr_attendance_report_views.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}