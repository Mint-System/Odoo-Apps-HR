# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "HR Timesheet Attendance Recording",
    "summary": """
        Create attendance records from timesheet entries.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Human Resources",
    "development_status": "Production/Stable",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_timesheet", "hr_attendance"],
    "data": [
        "views/hr_attendance.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
