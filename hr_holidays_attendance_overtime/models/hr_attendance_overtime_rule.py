# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class HrAttendanceOvertimeRule(models.Model):
    _inherit = "hr.attendance.overtime.rule"

    leave_type_id = fields.Many2one(
        "hr.leave.type",
        string="Time Off Type",
        domain="[('overtime_deductible', '=', True), ('requires_allocation', '=', False)]",
        help="Hours from this rule are credited to the balance of this time off type "
        "and can only be compensated with this time off type. "
        "If several rules apply, the rule with the highest sequence wins.",
    )
    max_extra_hours = fields.Float(
        string="Max Hours per Week",
        help="Maximum of worked hours per week this rule credits, e.g. 45 hours. "
        "The extra hours are the difference between this limit and the hours of the "
        "employee contract, e.g. 7 hours for a 38 hour contract. "
        "Leave empty for no limit.",
    )

    @api.constrains("leave_type_id")
    def _check_leave_type_id(self):
        """Ensure the linked time off type is a deductible type without allocation."""
        for rule in self.filtered("leave_type_id"):
            leave_type = rule.leave_type_id
            if not leave_type.overtime_deductible or leave_type.requires_allocation:
                raise ValidationError(
                    self.env._(
                        "The time off type '%(type)s' must have 'Deduct Extra Hours' "
                        "enabled and must not require an allocation.",
                        type=leave_type.name,
                    )
                )

    @api.constrains("max_extra_hours")
    def _check_max_extra_hours(self):
        """Ensure the weekly limit is not negative."""
        for rule in self.filtered("max_extra_hours"):
            if float_compare(rule.max_extra_hours, 0.0, precision_digits=2) < 0:
                raise ValidationError(
                    self.env._(
                        "Rule '%(name)s' has a negative maximum of extra hours.",
                        name=rule.name,
                    )
                )

    def _generate_overtime_vals_v2(self, min_check_in, max_check_out, attendances, schedules_intervals_by_employee):
        """Generate the overtime vals of the rules that credit a time off type.

        The core merges the intervals of all rules and splits the overlaps, so
        that the same hours are credited to only one rule. A weekly rule and a
        daily rule with a weekly limit credit different hours by design, the
        daily rule the hours up to the limit and the weekly rule the hours
        above it. Therefore the rules are generated separately and the vals are
        concatenated.
        """
        linked_rules = self.filtered(lambda rule: rule.leave_type_id or rule.max_extra_hours)
        other_rules = self - linked_rules
        if not linked_rules:
            return super()._generate_overtime_vals_v2(
                min_check_in, max_check_out, attendances, schedules_intervals_by_employee
            )
        vals_list = (
            super(HrAttendanceOvertimeRule, other_rules)._generate_overtime_vals_v2(
                min_check_in, max_check_out, attendances, schedules_intervals_by_employee
            )
            if other_rules
            else []
        )
        for rule in linked_rules:
            vals_list += super(HrAttendanceOvertimeRule, rule)._generate_overtime_vals_v2(
                min_check_in, max_check_out, attendances, schedules_intervals_by_employee
            )
        capped_rules = linked_rules.filtered("max_extra_hours")
        if capped_rules:
            vals_list = capped_rules._apply_max_extra_hours(vals_list)
        return vals_list

    def _apply_max_extra_hours(self, vals_list):
        """Remove the hours above the weekly limit from the vals of a rule.

        The excess is removed from the last days of the week, so the first days
        keep their hours.

        :param vals_list: overtime vals generated for the ruleset
        :return: the vals, without the durations above the weekly limit
        """
        capped_rule_ids = set(self.ids)
        hours_by_key = defaultdict(float)
        rule_by_key = {}
        for vals in vals_list:
            rule_ids = set(vals["rule_ids"])
            if not rule_ids & capped_rule_ids:
                continue
            week_start = vals["date"] - timedelta(days=vals["date"].weekday())
            key = (vals["employee_id"], week_start)
            hours_by_key[key] += vals["duration"]
            rule_by_key[key] = self.browse(rule_ids & capped_rule_ids).sorted("sequence")[0]
        limits = {key: rule_by_key[key]._get_max_extra_hours_for_employee(key[0], key[1]) for key in hours_by_key}
        ordered_vals = sorted(vals_list, key=lambda vals: (vals["date"], vals["time_start"]))
        durations = {}
        for index in reversed(range(len(ordered_vals))):
            vals = ordered_vals[index]
            if not set(vals["rule_ids"]) & capped_rule_ids:
                continue
            week_start = vals["date"] - timedelta(days=vals["date"].weekday())
            key = (vals["employee_id"], week_start)
            excess = hours_by_key[key] - limits[key]
            if float_compare(excess, 0.0, precision_digits=4) <= 0:
                continue
            duration = max(vals["duration"] - excess, 0.0)
            hours_by_key[key] -= vals["duration"] - duration
            durations[index] = duration
        result = []
        for index, vals in enumerate(ordered_vals):
            duration = durations.get(index, vals["duration"])
            if float_compare(duration, 0.0, precision_digits=4) > 0:
                result.append({**vals, "duration": round(duration, 4)})
        return result

    def _get_max_extra_hours_for_employee(self, employee_id, week_start):
        """Return the extra hours a rule may credit for an employee and week.

        :param employee_id: id of the employee
        :param week_start: first day of the week
        :return: the maximum of extra hours per week
        """
        self.ensure_one()
        employee = self.env["hr.employee"].browse(employee_id).sudo()
        version = employee._get_version(week_start)
        if not version:
            return self.max_extra_hours
        contract_hours = self._get_expected_hours_from_contract(week_start, version, period="week")
        return max(self.max_extra_hours - contract_hours, 0.0)
