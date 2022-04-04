{
    'name': "HR Holidays Calendar Department",

    'summary': """
        Adds department field and filters to report.
    """,
    
    'author': 'Mint System GmbH, Odoo Community Association (OCA)',
    'website': 'https://www.mint-system.ch',
    'category': 'Human Resources',
    'version': '14.0.1.0.0',
    'license': 'AGPL-3',
    
    'depends': ['hr_holidays_calendar'],

    'data': [
        'report/hr_leave_report_calendar_views.xml',
        'views/show_department.xml'
    ],

    'installable': True,
    'application': False,
    "images": ["images/screen.png"],
}