import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrPlanActivityType(models.Model):
    _inherit = "hr.plan.activity.type"

    activity_date_input = fields.Selection(
        [("start", "Start Date"), ("end", "End Date"), ("none", "None")],
        default="none",
        required=True,
    )
    activity_date_offset_days = fields.Integer()
