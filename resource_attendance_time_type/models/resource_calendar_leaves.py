# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    time_type = fields.Selection(selection_add=[('attendance', 'Attendance')])
    
