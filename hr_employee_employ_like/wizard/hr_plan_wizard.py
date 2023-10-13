import logging

from odoo import _, models

_logger = logging.getLogger(__name__)
from werkzeug.urls import url_encode


class HrPlanWizard(models.TransientModel):
    _inherit = "hr.plan.wizard"

    def _prepare_activity_values(self, activity_type, responsible, date_deadline=False):
        res = super()._prepare_activity_values(
            activity_type, responsible, date_deadline
        )
        if self.employee_id.employ_like_id:
            url = "/web#%s" % url_encode(
                {
                    "id": self.employee_id.employ_like_id.id,
                    "model": "hr.employee.public",
                    "view_mode": "form",
                    "menu_id": self.env.ref("hr.menu_hr_root").id,
                }
            )
            name = self.employee_id.employ_like_id.display_name
            res["note"] = (
                _('<b>Employ like:</b> <a href="%s">%s</a><br/>') % (url, name)
            ) + res["note"]
        return res
