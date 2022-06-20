{
    "name": "HR Recruitment Firstname",
    "summary": """
        First and lastname on applicant form.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Human Resources",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_recruitment", "partner_firstname", "website_hr_recruitment"],
    "data": [
        "views/hr_recruitment.xml",
        "views/website_hr_recruitment_templates.xml",
        "data/config_data.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
