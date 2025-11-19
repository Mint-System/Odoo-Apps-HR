import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    compensate_overtime = fields.Boolean(
        "Compensate Extra Hours",
        default=False,
        help="""Once a time off of this type is approved,
        the duration will be deducted from extra hours.""",
    )

    def get_allocation_data(self, employees, target_date=None):
        """
        Show extra hours even if they are negative.
        """
        res = super().get_allocation_data(employees, target_date)

        # Iterate through each employee in the result
        for employee, allocation_list in res.items():
            extra_hours_found = any(item[0] == "Extra Hours" for item in allocation_list)
            if not extra_hours_found:
                extra_hours_data = (
                    "Extra Hours",
                    {
                        "remaining_leaves": 0,
                        "virtual_remaining_leaves": employee.sudo().total_overtime,
                        "max_leaves": 0,
                        "accrual_bonus": 0,
                        "leaves_taken": 0,
                        "virtual_leaves_taken": 0,
                        "leaves_requested": 0,
                        "leaves_approved": 0,
                        "closest_allocation_remaining": 0,
                        "closest_allocation_expire": False,
                        "closest_allocation_duration": False,
                        "holds_changes": False,
                        "total_virtual_excess": 0,
                        "virtual_excess_data": {},
                        "exceeding_duration": 0,
                        "request_unit": "hour",
                        "icon": "/hr_holidays/static/src/img/icons/Extra_Time_Off.svg",
                        "allows_negative": True,
                        "max_allowed_negative": 9999,
                        "overtime_deductible": True,
                    },
                    "no",
                    -1,
                )
                allocation_list.append(extra_hours_data)

        return res
