# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Hr Employee Attendance Report Balances",
    "summary": """
        Adds balances to attendance report.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_employee_attendance_report"],
    "data": [
        "report/hr_employee_report.xml",
        "data/hr_employee_data.xml"],
    'assets': {
        'web.assets_backend': [
            'hr_employee_attendance_report_balances/static/src/css/report_styles.css',
        ],
        'web.report_assets_common': [
            'hr_employee_attendance_report_balances/static/src/css/report_styles.css',
        ],
        'web.report_assets_pdf': [
            'hr_employee_attendance_report_balances/static/src/css/report_styles.css',
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    
}
