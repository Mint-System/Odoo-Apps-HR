{
    "name": "HR Attendance Missing Contract",
    "summary": """
        Create missing attendances only for employees under contract.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance_missing", "hr_contract"],
    "data": ["wizard/select_period.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
