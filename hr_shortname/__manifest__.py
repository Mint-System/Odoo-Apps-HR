{
    'name': "HR Shortname",

    'summary': """
        Set public shortname foreach employee.
    """,
    
    'author': 'Mint System GmbH, Odoo Community Association (OCA)',
    'website': 'https://www.mint-system.ch',
    'category': 'Human Resources',
    'version': '14.0.1.0.0',
    'license': 'AGPL-3',
    
    'depends': ['hr'],

    'data': [
        'views/hr_employee_views.xml',
        'views/hr_employee_public_views.xml',
    ],

    'installable': True,
    'application': False,
    "images": ["images/screen.png"],
}