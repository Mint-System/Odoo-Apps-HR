# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Hr Contract Leaves Domain",
    "summary": """
        Changes the method "_get_expected_attendances" in hr_contract/models/hr_employee.py to only take intervals with time_type 'leave' and 'attendance'.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_contract", "resource_attendance_time_type"],
    "data": ["security/security.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    
}
