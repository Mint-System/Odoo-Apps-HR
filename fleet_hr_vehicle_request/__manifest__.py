{
    "name": "Fleet HR Vehicle Request",
    "summary": """
        Bridge module for fleet and employee vehicle request.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Human Resources",
    "version": "13.0.2.0.0",
    "license": "AGPL-3",
    "depends": ["hr_vehicle_request"],
    "data": ["views/vehicle_request.xml", "views/fleet_vehicle.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
