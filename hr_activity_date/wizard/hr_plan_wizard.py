import logging

from odoo import _, models

_logger = logging.getLogger(__name__)
from datetime import timedelta

from odoo.exceptions import UserError


class HrPlanWizard(models.TransientModel):
    _inherit = "hr.plan.wizard"

    def _get_plan_activity_schedule_values(self, activity_type, employee, responsible, date_deadline):
        """Hook to insert values"""
        return {
            "activity_type_id": activity_type.activity_type_id.id,
            "summary": activity_type.summary,
            "note": activity_type.note or "",
            "user_id": responsible.id,
            "date_deadline": date_deadline,
        }

    def action_launch(self):
        self.ensure_one()
        for employee in self.employee_ids:
            contract_id = employee.contract_id
            if not contract_id:
                raise UserError(_("This user does not have an active contract."))

            body = _("The plan %s has been started", self.plan_id.name)
            activities = set()

            for activity_type in self._get_activities_to_schedule():
                responsible = activity_type.get_responsible_id(employee)["responsible"]

                if self.env["hr.employee"].with_user(responsible).check_access_rights("read", raise_exception=False):
                    date_deadline = self.env["mail.activity"]._calculate_date_deadline(activity_type.activity_type_id)

                    # Overwrite date deadline with contract date
                    if activity_type.activity_date_input == "start" and contract_id.date_start:
                        date_deadline = contract_id.date_start
                    if activity_type.activity_date_input == "end" and contract_id.date_end:
                        date_deadline = contract_id.date_end

                    # Apply offset
                    if activity_type.activity_date_offset_days != 0:
                        date_deadline = date_deadline + timedelta(days=activity_type.activity_date_offset_days)

                    # Hook for custom values (note, etc.)
                    schedule_values = self._get_plan_activity_schedule_values(
                        activity_type, employee, responsible, date_deadline
                    )
                    employee.activity_schedule(**schedule_values)

                    activity = _(
                        "%(activity)s, assigned to %(name)s, due on the %(deadline)s",
                        activity=activity_type.summary,
                        name=responsible.name,
                        deadline=date_deadline,
                    )
                    activities.add(activity)

            if activities:
                body += "<ul>"
                for activity in activities:
                    body += "<li>%s</li>" % activity
                body += "</ul>"
            employee.message_post(body=body)

        if len(self.employee_ids) == 1:
            return {
                "type": "ir.actions.act_window",
                "res_model": "hr.employee",
                "res_id": self.employee_ids.id,
                "name": self.employee_ids.display_name,
                "view_mode": "form",
                "views": [(False, "form")],
            }
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.employee",
            "name": _("Launch Plans"),
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("id", "in", self.employee_ids.ids)],
        }
