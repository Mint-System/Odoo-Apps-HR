import logging

from odoo import models

_logger = logging.getLogger(__name__)


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    def get_employees_days(self, employee_ids):
        """OVERWRITE include archived leaves in leaves calculation"""
        # result = super(HolidaysType, self).get_employees_days(employee_ids)

        result = {
            employee_id: {
                leave_type.id: {
                    "max_leaves": 0,
                    "leaves_taken": 0,
                    "remaining_leaves": 0,
                    "virtual_remaining_leaves": 0,
                }
                for leave_type in self
            }
            for employee_id in employee_ids
        }

        requests = self.env["hr.leave"].search(
            [
                ("active", "in", [True, False]),
                ("employee_id", "in", employee_ids),
                ("state", "in", ["confirm", "validate1", "validate"]),
                ("holiday_status_id", "in", self.ids),
            ]
        )

        allocations = self.env["hr.leave.allocation"].search(
            [
                ("employee_id", "in", employee_ids),
                ("state", "in", ["confirm", "validate1", "validate"]),
                ("holiday_status_id", "in", self.ids),
            ]
        )

        for request in requests:
            status_dict = result[request.employee_id.id][request.holiday_status_id.id]
            status_dict["virtual_remaining_leaves"] -= (
                request.number_of_hours_display
                if request.leave_type_request_unit == "hour"
                else request.number_of_days
            )
            if request.state == "validate":
                status_dict["leaves_taken"] += (
                    request.number_of_hours_display
                    if request.leave_type_request_unit == "hour"
                    else request.number_of_days
                )
                status_dict["remaining_leaves"] -= (
                    request.number_of_hours_display
                    if request.leave_type_request_unit == "hour"
                    else request.number_of_days
                )

        for allocation in allocations.sudo():
            status_dict = result[allocation.employee_id.id][
                allocation.holiday_status_id.id
            ]
            if allocation.state == "validate":
                # note: add only validated allocation even for the virtual
                # count; otherwise pending then refused allocation allow
                # the employee to create more leaves than possible
                status_dict["virtual_remaining_leaves"] += (
                    allocation.number_of_hours_display
                    if allocation.type_request_unit == "hour"
                    else allocation.number_of_days
                )
                status_dict["max_leaves"] += (
                    allocation.number_of_hours_display
                    if allocation.type_request_unit == "hour"
                    else allocation.number_of_days
                )
                status_dict["remaining_leaves"] += (
                    allocation.number_of_hours_display
                    if allocation.type_request_unit == "hour"
                    else allocation.number_of_days
                )
        return result
