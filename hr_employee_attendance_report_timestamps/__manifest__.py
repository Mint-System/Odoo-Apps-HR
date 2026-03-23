# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Hr Employee Attendance Report Timestamps",
    "summary": """
        Adds timestamp column to report.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base", "hr_employee_attendance_report"],
    "data": [
        "report/hr_employee_report.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_employee_attendance_report_timestamps/static/src/css/attendance.css",
            "hr_employee_attendance_report_timestamps/static/src/js/attendance_list_reload.js",
        ],
        "web.report_assets_common": [
            "hr_employee_attendance_report_timestamps/static/src/css/report_styles.css",
            "hr_employee_attendance_report_timestamps/static/src/css/attendance.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
