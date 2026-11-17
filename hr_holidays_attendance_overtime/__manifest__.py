# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "HR Holidays Attendance Overtime",
    "summary": """
        Link overtime rules to time off types to keep separate extra hours and overtime balances.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Human Resources/Attendances",
    "development_status": "Production/Stable",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_holidays_attendance"],
    "data": [
        "data/hr_leave_type.xml",
        "data/hr_attendance_overtime_ruleset.xml",
        "views/hr_attendance_overtime_ruleset.xml",
        "views/hr_attendance_overtime_rule.xml",
        "views/hr_leave_type.xml",
        "views/hr_attendance.xml",
        "views/hr_attendance_overtime_line.xml",
    ],
    "demo": [
        "demo/hr_attendance_demo.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
