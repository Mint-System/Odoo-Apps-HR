from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    """Recreate the attendance report view after all tables exist."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['hr.attendance.report'].init()
