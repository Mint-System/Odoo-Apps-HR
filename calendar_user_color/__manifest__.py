# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Calendar User Color",
    "summary": """
        Module summary.
    """,
    "author": "Mint System GmbH",
    "website": "https://github.com/OCA/sale-workflow",
    "category": "Repository",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base", "calendar"],
    "data": [
        "views/calendar_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    "assets": {
        "web.assets_backend": [
            "calendar_user_color/static/src/views/attendee_calendar/attendee_calendar_model_color.js",
        ]
    },
}
