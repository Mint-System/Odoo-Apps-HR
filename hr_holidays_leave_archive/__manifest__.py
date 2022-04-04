{
    'name': "HR Holidays Leave Archive",

    'summary': """
        Enables archiving of time off / hr leave entries.
    """,
    
    'author': 'Mint System GmbH, Odoo Community Association (OCA)',
    'website': 'https://www.mint-system.ch',
    'category': 'Human Resources',
    'version': '14.0.1.0.0',
    'license': 'AGPL-3',
    
    'depends': ['hr_holidays'],


    'data': [
        'views/hr_leave_views.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
    "images": ["images/screen.png"],
}