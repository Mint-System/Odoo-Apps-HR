{
    "name": "HR Vehicle Request Calendar",
    "summary": """
        Calendar views for vehicle requests and confirmation message with .ics file.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Human Resources",
    "version": "14.0.3.0.0",
    "license": "AGPL-3",
    "depends": ["hr_vehicle_request", "calendar"],
    "data": ["views/employee_fleet.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
