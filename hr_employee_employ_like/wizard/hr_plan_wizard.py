import logging

from odoo import _, models

_logger = logging.getLogger(__name__)
from werkzeug.urls import url_encode


class HrPlanWizard(models.TransientModel):
    _inherit = "hr.plan.wizard"

    def _get_plan_activity_schedule_values(self, activity_type, employee, responsible, date_deadline):
        res = super()._get_plan_activity_schedule_values(activity_type, employee, responsible, date_deadline)

        if employee.employ_like_id:
            url = "/web#%s" % url_encode(
                {
                    "id": employee.employ_like_id.id,
                    "model": "hr.employee.public",
                    "view_mode": "form",
                    "menu_id": self.env.ref("hr.menu_hr_root").id,
                }
            )
            name = employee.employ_like_id.display_name
            note = res.get("note") or ""
            res["note"] = (_('<b>Employ like:</b> <a href="%s">%s</a><br/>') % (url, name)) + note

        return res
