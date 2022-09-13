{
    "name": "HR Attendance Kiosk Mode Color",
    "summary": """
        Colored backgrounds for the attendance kiosk mode.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Human Resources",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_kiosk_mode_color/static/src/js/kiosk.js",
            "hr_attendance_kiosk_mode_color/static/src/scss/kiosk.scss",
        ]
    },
}
