import logging

from datetime import datetime, time, timedelta

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    

    def calculate_missing_break(self):
        leave_missing_break = self.env["hr.leave.type"].search([("code", "=", "MB"), ("company_id", "=", self.env.company.id)])
        if not leave_missing_break:
            leave_missing_break = self.env["hr.leave.type"].create({"name": "Missing Break", "code": "MB", "requires_allocation": "no", "leave_validation_type": "no_validation", "company_id": self.env.company.id})

        _logger.warning("leave_missing_break: %s" % (leave_missing_break))

        attendance = self
        employee = attendance.employee_id
        check_in = attendance.check_in
        check_out = attendance.check_out

        leave_missing_break_date = check_in.date()
        t_start = time(10, 00)
        t_end = time(10, 30)
        break_start_date = datetime.combine(leave_missing_break_date, t_start)
        break_end_date = datetime.combine(leave_missing_break_date, t_end)

        existing_leave = self.env["hr.leave"].search([
            ("employee_id", "=", employee.id),
            ("holiday_status_id", "=", leave_missing_break.id),
            ("date_from", "<=", leave_missing_break_date),
            ("date_to", ">=", leave_missing_break_date),
        ], limit=1)


        if check_out - check_in > timedelta(hours=7):
            if not existing_leave:
                self.env["hr.leave"].create({"employee_id": employee.id, "holiday_type": "employee", "holiday_status_id": leave_missing_break.id, "date_from": break_start_date, "date_to": break_end_date })
                not_title = "Missing break added"
                not_type = "success"
                not_message = f"A missing break for {employee.name} was added."
            else:
                not_title = "Missing break already exists"
                not_type = "warning"
                not_message = "Missing break for this day and employee already exists."
        else:
            not_title = "No Missing Break added"
            not_type = "warning"
            not_message = "Working hours are less than 7 hrs. No missing break created."

        return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": not_title,
                    "message": not_message,
                    "type": not_type,
                    "sticky": False,
                },
        }