# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Enable the display of extra hours, the balances are shown on the employee."""
    env["res.company"].search([]).hr_attendance_display_overtime = True
