# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import api, fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    weekly_overtime_hours = fields.Float(
        string="Weekly Overtime Hours",
        compute="_compute_weekly_overtime_hours",
        store=True,
        help="Hours of the overtime rules with a weekly period, e.g. the hours above "
        "the weekly limit. They are shown on the last attendance of the week.",
    )

    @api.depends("check_in", "check_out", "employee_id")
    def _compute_overtime_hours(self):
        """Count only the extra hours, the weekly overtime is shown separately."""
        for attendance in self:
            attendance.overtime_hours = sum(attendance._get_extra_hours_lines().mapped("duration"))

    @api.depends("check_in", "check_out", "employee_id")
    def _compute_validated_overtime_hours(self):
        """Count only the approved extra hours, the weekly overtime is shown separately."""
        for attendance in self:
            extra_hours = attendance._get_extra_hours_lines()
            attendance.validated_overtime_hours = sum(
                extra_hours.filtered_domain([("status", "=", "approved")]).mapped("manual_duration")
            )

    def _get_extra_hours_lines(self):
        """Return the overtime lines of the attendance that are extra hours.

        The lines of rules with a weekly period are weekly overtime, they are
        shown in the field `weekly_overtime_hours`.

        :return: the overtime lines that are extra hours
        """
        self.ensure_one()
        return self.linked_overtime_ids.filtered(
            lambda line: not any(rule.quantity_period == "week" for rule in line.rule_ids)
        )

    def _compute_weekly_overtime_hours(self):
        """Sum the hours of the weekly rules on the last attendance of the week.

        The weekly rules credit the hours above a weekly limit, e.g. the hours
        above 45 hours. They are not extra hours, therefore they are shown in a
        separate field and only on the last attendance of the week.
        """
        for attendance in self:
            attendance.weekly_overtime_hours = 0.0
        if not self:
            return
        lines = (
            self.env["hr.attendance.overtime.line"]
            .sudo()
            .search(
                [
                    ("employee_id", "in", self.employee_id.ids),
                    ("status", "=", "approved"),
                    ("rule_ids.quantity_period", "=", "week"),
                ]
            )
        )
        if not lines:
            return
        # The hours of a week are shown on the last attendance of the week
        last_attendance_by_key = {}
        for attendance in self.sorted(lambda att: (att.check_in, att.id)):
            last_attendance_by_key[self._get_week_key(attendance)] = attendance
        hours_by_key = {}
        for line in lines:
            key = self._get_week_key(line)
            hours_by_key[key] = hours_by_key.get(key, 0.0) + line.manual_duration
        for key, hours in hours_by_key.items():
            attendance = last_attendance_by_key.get(key)
            if attendance:
                attendance.weekly_overtime_hours = hours

    def _get_week_key(self, record):
        """Return the key of the employee and the week of an attendance or line.

        :param record: an attendance or an overtime line
        :return: the employee id and the first day of the week
        """
        date = record.date
        return (record.employee_id.id, date - timedelta(days=date.weekday()))
