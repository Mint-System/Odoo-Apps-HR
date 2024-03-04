{
    "name": "HR Holidays Negative Hours",
    "summary": """
        Allow submit time-off request with negative extra hours.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr"],
    "data": [
        "data/hr_leave_type.xml",
        "view/hr_leave_type.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
