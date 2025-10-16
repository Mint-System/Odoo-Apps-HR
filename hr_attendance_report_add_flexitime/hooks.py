from odoo import fields, api, SUPERUSER_ID
from datetime import date

def post_init_hook(cr, registry):
    """Recreate the attendance report view after all tables exist."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    model = env['hr.employee.planned.hours']

    today = fields.Date.today()
    year_start = date(today.year, 1, 1)

    # Build planned hours from Jan 1 to today
    model.compute_planned_hours(year_start, today)

    env['hr.attendance.report'].init()
