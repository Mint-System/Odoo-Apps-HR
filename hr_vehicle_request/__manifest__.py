{
    "name": "HR Vehicle Request",
    "summary": """
        Employees can request and reserve cars.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Human Resources",
    "version": "13.0.1.2.0",
    "license": "AGPL-3",
    "depends": ["hr", "fleet"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/employee_fleet.xml",
        "data/data.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
