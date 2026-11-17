# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timedelta

from pytz import utc

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestOvertimeLeaveType(TransactionCase):
    """Test the link between an overtime rule and a time off type."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "Overtime Company"})
        cls.user = new_test_user(
            cls.env,
            login="overtime_user",
            groups="base.group_user",
            company_id=cls.company.id,
        ).with_company(cls.company)
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Overtime Employee",
                "user_id": cls.user.id,
                "company_id": cls.company.id,
            }
        )
        cls.leave_type_extra_hours = cls.env["hr.leave.type"].create(
            {
                "name": "Test Extra Hours",
                "company_id": cls.company.id,
                "requires_allocation": False,
                "overtime_deductible": True,
            }
        )
        cls.leave_type_overtime = cls.env["hr.leave.type"].create(
            {
                "name": "Test Overtime",
                "company_id": cls.company.id,
                "requires_allocation": False,
                "overtime_deductible": True,
            }
        )
        cls.calendar_38_hours = cls.env["resource.calendar"].create(
            {
                "name": "38 Hours",
                "company_id": cls.company.id,
                "tz": "UTC",
                "attendance_ids": [
                    Command.create(
                        {
                            "name": str(day),
                            "dayofweek": str(day),
                            "hour_from": 8,
                            "hour_to": 15.6,
                            "day_period": "morning",
                        }
                    )
                    for day in range(5)
                ],
            }
        )
        cls.ruleset = cls.env["hr.attendance.overtime.ruleset"].create(
            {
                "name": "Test Ruleset",
                "company_id": cls.company.id,
                "rule_ids": [
                    Command.create(
                        {
                            "name": "Test Extra Hours Rule",
                            "base_off": "quantity",
                            "quantity_period": "day",
                            "expected_hours_from_contract": True,
                            "compensable_as_leave": True,
                            "leave_type_id": cls.leave_type_extra_hours.id,
                            "sequence": 10,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Test Overtime Rule",
                            "base_off": "quantity",
                            "quantity_period": "week",
                            "expected_hours_from_contract": False,
                            "expected_hours": 45.0,
                            "compensable_as_leave": True,
                            "leave_type_id": cls.leave_type_overtime.id,
                            "sequence": 20,
                        }
                    ),
                ],
            }
        )
        cls.rule_extra_hours = cls.ruleset.rule_ids.filtered(
            lambda rule: rule.leave_type_id == cls.leave_type_extra_hours
        )
        cls.rule_overtime = cls.ruleset.rule_ids.filtered(lambda rule: rule.leave_type_id == cls.leave_type_overtime)

    def _create_overtime_line(self, rules, duration, status="approved", day=date(2025, 1, 6)):
        """Create an overtime line with the given rules and duration."""
        return self.env["hr.attendance.overtime.line"].create(
            {
                "employee_id": self.employee.id,
                "date": day,
                "time_start": datetime.combine(day, datetime.min.time()),
                "time_stop": datetime.combine(day, datetime.min.time()) + timedelta(hours=max(duration, 1)),
                "duration": duration,
                "rule_ids": [Command.set(rules.ids)],
                "compensable_as_leave": True,
                "status": status,
            }
        )

    def test_rule_leave_type_link(self):
        """The time off type is visible on the linked rule and vice versa."""
        self.assertEqual(self.rule_overtime.leave_type_id, self.leave_type_overtime)
        self.assertEqual(self.leave_type_overtime.overtime_rule_ids, self.rule_overtime)
        self.assertTrue(self.leave_type_overtime._is_linked_overtime_type())

    def test_line_leave_type_from_rule(self):
        """An overtime line gets the time off type of its rule."""
        line = self._create_overtime_line(self.rule_extra_hours, 2.0)
        self.assertEqual(line.overtime_leave_type_id, self.leave_type_extra_hours)

    def test_deciding_rule_by_sequence(self):
        """The rule with the highest sequence decides the time off type."""
        line = self._create_overtime_line(self.rule_extra_hours | self.rule_overtime, 2.0)
        self.assertEqual(line.overtime_leave_type_id, self.leave_type_overtime)

    def test_balance_per_leave_type(self):
        """Overtime lines are credited to the balance of their time off type."""
        self._create_overtime_line(self.rule_extra_hours, 3.0)
        self._create_overtime_line(self.rule_overtime, 5.0)
        balances = self.employee._get_overtime_leave_type_balances()[self.employee.id]
        self.assertAlmostEqual(balances[self.leave_type_extra_hours.id]["earned"], 3.0)
        self.assertAlmostEqual(balances[self.leave_type_overtime.id]["earned"], 5.0)
        self.assertAlmostEqual(balances[self.leave_type_overtime.id]["balance"], 5.0)

    def test_invalid_leave_type(self):
        """A time off type that requires an allocation cannot be linked."""
        leave_type_with_allocation = self.env["hr.leave.type"].create(
            {
                "name": "Test Allocation",
                "company_id": self.company.id,
                "requires_allocation": True,
                "overtime_deductible": True,
            }
        )
        with self.assertRaises(ValidationError):
            self.rule_overtime.leave_type_id = leave_type_with_allocation

    def test_max_extra_hours(self):
        """The hours above the weekly limit are not credited to the extra hours rule."""
        self.rule_extra_hours.max_extra_hours = 45.0
        self._set_38_hours_contract()
        # 5 days with 11 h worked and a contract of 7.6 h per day
        attendances = self._create_attendances(date(2025, 1, 6), 5, 11.0)
        vals_list = self._generate_overtime_vals(attendances)
        extra_hours = sum(vals["duration"] for vals in vals_list if vals["rule_ids"] == self.rule_extra_hours.ids)
        # 5 x 3.4 h are capped to the 7 h between the 45 h limit and the 38 h contract
        self.assertAlmostEqual(extra_hours, 7.0)

    def test_no_max_extra_hours(self):
        """Without a limit all hours are credited to the extra hours rule."""
        self._set_38_hours_contract()
        attendances = self._create_attendances(date(2025, 1, 6), 5, 11.0)
        vals_list = self._generate_overtime_vals(attendances)
        extra_hours = sum(vals["duration"] for vals in vals_list if vals["rule_ids"] == self.rule_extra_hours.ids)
        self.assertAlmostEqual(extra_hours, 17.0)

    def test_overtime_and_extra_hours_do_not_overlap(self):
        """The hours of the extra hours rule and the overtime rule are distinct."""
        self.rule_extra_hours.max_extra_hours = 45.0
        self.rule_overtime.expected_hours = 45.0
        self._set_38_hours_contract()
        attendances = self._create_attendances(date(2025, 1, 6), 5, 11.0)
        vals_list = self._generate_overtime_vals(attendances)
        extra_hours = sum(vals["duration"] for vals in vals_list if vals["rule_ids"] == self.rule_extra_hours.ids)
        overtime = sum(vals["duration"] for vals in vals_list if vals["rule_ids"] == self.rule_overtime.ids)
        # 55 h worked, 38 h contract and a 45 h weekly limit
        self.assertAlmostEqual(extra_hours, 7.0)
        self.assertAlmostEqual(overtime, 10.0)
        # No hours are lost and none is counted twice
        self.assertAlmostEqual(extra_hours + overtime, 55.0 - 38.0)

    def test_weekly_overtime_hours(self):
        """The weekly overtime is shown separately on the last attendance of the week."""
        self.rule_extra_hours.max_extra_hours = 45.0
        self._set_38_hours_contract()
        attendances = self._create_attendances(date(2025, 1, 6), 5, 11.0)
        vals_list = self._generate_overtime_vals(attendances)
        self.env["hr.attendance.overtime.line"].search([("employee_id", "=", self.employee.id)]).unlink()
        self.env["hr.attendance.overtime.line"].create(vals_list)
        attendances.invalidate_recordset()
        attendances._compute_weekly_overtime_hours()
        attendances._compute_validated_overtime_hours()
        last_attendance = attendances.sorted("check_in")[-1]
        # 55 h worked, 38 h contract and a 45 h weekly limit
        self.assertAlmostEqual(last_attendance.weekly_overtime_hours, 10.0)
        # The extra hours fields do not contain the weekly overtime
        self.assertAlmostEqual(last_attendance.validated_overtime_hours, 0.0)
        self.assertAlmostEqual(sum(attendances.mapped("validated_overtime_hours")), 7.0)
        # The weekly overtime is shown on the last attendance only
        self.assertAlmostEqual(sum(attendances.mapped("weekly_overtime_hours")), 10.0)

    def _set_38_hours_contract(self):
        """Set a 38 h contract that covers the test dates."""
        self.employee.resource_calendar_id = self.calendar_38_hours
        self.employee.version_ids.write(
            {
                "resource_calendar_id": self.calendar_38_hours.id,
                "contract_date_start": date(2024, 1, 1),
                "ruleset_id": self.ruleset.id,
            }
        )

    def _create_attendances(self, first_day, days, hours_per_day):
        """Create attendances of the given hours starting at 08:00."""
        attendances = self.env["hr.attendance"]
        for day in range(days):
            check_in = datetime.combine(first_day + timedelta(days=day), datetime.min.time()) + timedelta(hours=8)
            attendances |= self.env["hr.attendance"].create(
                {
                    "employee_id": self.employee.id,
                    "check_in": check_in,
                    "check_out": check_in + timedelta(hours=hours_per_day),
                }
            )
        return attendances

    def _generate_overtime_vals(self, attendances):
        """Generate the overtime vals of the ruleset for the attendances."""
        min_check_in = utc.localize(min(attendances.mapped("check_in")))
        max_check_out = utc.localize(max(attendances.mapped("check_out")))
        version_periods = self.employee.sudo()._get_version_periods(min_check_in, max_check_out)
        schedules = self.employee._get_schedules_by_employee_by_work_type(min_check_in, max_check_out, version_periods)
        return self.ruleset.rule_ids._generate_overtime_vals_v2(min_check_in, max_check_out, attendances, schedules)
