# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Hr Payslip Report Manual Note",
    "summary": """
        Adds a text Field to the payslip that appears at the bottom of the swiss payslip.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_payroll", "l10n_ch_hr_payroll_elm_transmission"],
    "data": [
        "views/hr_payslip_views.xml",
        "views/hr_payslip_report_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    
}
