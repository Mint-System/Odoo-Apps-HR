{
    "name": "HR Expense Vehicle Request",
    "summary": """
        Create expenses from retourned vehicle requests.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Human Resources",
    "version": "14.0.3.0.0",
    "license": "AGPL-3",
    "depends": ["hr_expense", "fleet_hr_vehicle_request"],
    "data": [
        "data/hr_expense.xml",
        "views/hr_expense.xml",
        "views/vehicle_request.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
