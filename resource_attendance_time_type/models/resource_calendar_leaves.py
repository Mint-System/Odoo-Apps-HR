# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    time_type = fields.Selection([('leave', 'Time Off'), ('other', 'Other'), ('attendance', 'Attendance')], default='leave',
                                 help="Whether this should be computed as a time off or as work time (eg: formation)")
