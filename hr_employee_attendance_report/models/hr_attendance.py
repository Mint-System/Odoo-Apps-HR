import logging

from datetime import datetime, time, timedelta

from odoo import fields, models, api

_logger = logging.getLogger(__name__)

BREAK_DURATION_HOURS = 0.5


class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    has_missing_break = fields.Boolean(
        string="Missing Break",
    #    compute="_compute_has_missing_break",
        store=True
    )
    check_out_display = fields.Char(
        string="Check Out",
        compute="_compute_check_out_display",
        store=False
    )


    @api.depends('check_out', 'has_missing_break')
    def _compute_check_out_display(self):
        for att in self:
            if att.check_out:
                val = fields.Datetime.to_string(att.check_out)
                att.check_out_display = val + ("*" if att.has_missing_break else "")
            else:
                att.check_out_display = False

    @api.depends('employee_id', 'check_in')
    def _compute_has_missing_break(self):
        HrMissingBreak = self.env["hr.missing.break"]
        for att in self:
            att.has_missing_break = False
            if not att.employee_id or not att.check_in:
                continue
            att_date = fields.Date.to_date(att.check_in)
            exists = HrMissingBreak.search_count([
                ('employee_id', '=', att.employee_id.id),
                ('working_day', '=', att_date),
            ], limit=1)
            att.has_missing_break = bool(exists)

    def create_or_delete_missing_break(self):
        attendance = self
        employee = attendance.employee_id
        check_in = attendance.check_in
        check_out = attendance.check_out
        missing_break_date = check_in.date()

        existing_break = self.env["hr.missing.break"].search([
            ("employee_id", "=", employee.id),
            ("working_day", "=", missing_break_date),
        ], limit=1)

        if existing_break:
            self.deduct_or_add_missing_break(mbreak=existing_break, action='add')
            existing_break.unlink()

            self.has_missing_break = False
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Missing break removed, overtime added",
                    "message": f"The missing break for {employee.name} was removed and overtime added.",
                    "type": "success",
                    "sticky": False,
                },
            }

        if check_out - check_in > timedelta(hours=7):
            new_break = self.env["hr.missing.break"].create({"employee_id": employee.id, "working_day": missing_break_date})
            self.deduct_or_add_missing_break(mbreak=new_break, action='deduct')
            self.has_missing_break = True
            not_title = "Missing break added, overtime deducted"
            not_type = "success"
            not_message = f"A missing break for {employee.name} was added and overtime deducted."
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

    def deduct_or_add_missing_break(self, mbreak, action):
        OvertimeModel = self.env['hr.attendance.overtime']
        AttendanceModel = self.env['hr.attendance']

        if not mbreak:
            return False

        employee = mbreak.employee_id
        # Normalise to a date for comparison (working_day is Datetime)
        day_date = fields.Date.context_today(
            self, timestamp=mbreak.working_day
        )
        overtime = OvertimeModel.search([
                ('employee_id', '=', employee.id),
                ('date', '=', day_date),
            ], limit=1)

        # Find the overtime record for this employee / day
        # hr.attendance.overtime stores one record per employee per day.
        if action == "add" and overtime: 
            # Adjust existing overtime (can go negative — intentional)
            new_duration = overtime.duration + BREAK_DURATION_HOURS
            overtime.write({'duration': new_duration, 'adjustment': True})
            mbreak.write({
                'deducted': False,
                'deducted_on': fields.Datetime.now(),
            })
            return "added"
                
        if action == "deduct" and not mbreak.deducted:
            if overtime:
                new_duration = overtime.duration - BREAK_DURATION_HOURS
                overtime.write({'duration': new_duration, 'adjustment': True})
            else:
                OvertimeModel.create({
                    'employee_id': employee.id,
                    'date': day_date,
                    'duration': -BREAK_DURATION_HOURS,
                    'adjustment': True,   # marks it as a manual adjustment
                })

            # Mark as deducted — idempotency guard
            mbreak.write({
                'deducted': True,
                'deducted_on': fields.Datetime.now(),
            })
 
            return "deducted"
        
