{
    "name": "HR Employee Attendance Report",
    "summary": """
        Attendance and leave report.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance", "hr_holidays", "hr_holidays_remaining_leaves", "hr_leave_type_code", "float_align_at_decimal"],
    "data": [
        "report/hr_employee_report.xml",
        "report/res_users_report.xml",
        "security/ir.model.access.csv",
        "wizard/select_period.xml",
        "views/hr_attendance_views.xml",
        "views/hr_missing_break_views.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    'assets': {
        'web.assets_backend': [
          'hr_employee_attendance_report/static/src/css/attendance.css',
          'hr_employee_attendance_report/static/src/js/attendance_list_reload.js',
        ],
        'web.report_assets_common': [
            'hr_employee_attendance_report/static/src/css/report_styles.css',
            'hr_employee_attendance_report/static/src/css/attendance.css',
        ],
        'web.report_assets_pdf': [
            'hr_employee_attendance_report/static/src/css/report_styles.css',
        ],
    }

}

