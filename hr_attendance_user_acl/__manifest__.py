{
    "name": "HR Attendance User ACL",
    "summary": """
          Restrict user access rights to hr attendance entries.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Human Resources",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance"],
    "data": [
        "security/hr_attendance_security.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
