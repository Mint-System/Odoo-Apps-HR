# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Resource Attendance Time Type",
    "summary": """
        Adds the option to change the time_type in public holidays and adds 'attendance' as additonal type.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["resource"],
    "data": [
        "views/resource_calendar_leaves_list_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    
}
