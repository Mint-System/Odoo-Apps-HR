{
    "name": "Hr Attendance Missing",
    "summary": """
        Module summary.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Purchase,Technical,Accounting,Invoicing,Sales,Human Resources,Services,Helpdesk,Manufacturing,Website,Inventory,Administration,Productivity",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "report/invoice_document.xml",
        "data/ir_sequence.xml",
        "views/assets.xml",
        "views/sale_order.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    "qweb": ["static/src/xml/board.xml"],
    "demo": ["demo/demo.xml"],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_missing/static/src/js/action_refresh.js",
        ],
        "web.assets_qweb": [
            "hr_attendance_missing/static/src/xml/listview_refresh.xml",
        ],
    },
}