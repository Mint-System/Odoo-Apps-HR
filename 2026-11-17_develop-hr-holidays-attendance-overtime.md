---
commit_ref: 0ab6686bcfe130501de2c98eda1526e8ccacb02b
title: "Develop HR Holidays Attendance Overtime"
author: "Janik von Rotz <login@janikvonrotz.ch>"
session_id: 01a1e9e5-f5be-7016-aa75-bce357cdbb69
action: execute
state: completed
date_completed: 2026-11-17
harness: pi
provider: mistral
model: deepseek-v4-1-flash-1017
input_tokens: 1236080
output_tokens: 198471
---

# Develop HR Holidays Attendance Overtime

Note: @Clanker refers to the "ai agent" (you) who is working on this prompt file.

@Clanker when working on this prompt file, make sure to:

- Read the `AGENTS.md` to get an understanding of the project
- Read task section and prepare a list of todos
- Update the todo list while working on task

## Task

Implment a module "HR Holidays Attendance Overtime" / `hr_holidays_attendance_overtime` this folder.

I have used `create-module` to bootstrap the module.

This module is a re-implementation of `~/smartme-ecarup/smartme_overtime_split`. Checkout this module.

There are a few problems with the prototype:

- views.xml should be splitted per model
- German words used instead of translation
- Missing comments in methods

```python
def method_xy(self):
  """
  Comment
  """
  
```

For clarificaton "Extra Hours" -> "Überstunden" and "Overtime" -> "Überzeit".

Extra hours is calculated when the employee has more worked hours than expected hours. This works out of the box.

The overtime is second overtime rule that is connected to a new `hr.leave.type`. When working more than 45 hours a week the extra hours must be book a time off request of this type.

Setup a extra hours and overtime rules in data. Also setup the new hr.leave.type in data.

No demo data required.

Translate the module to german by using the `generate-module-translation` command.

Always use the `generate-module-*` commands to bootstrap models, views, ...

### Constraints

Requirements given by the author while reviewing the module:

- Installing the module must enable the setting *Display Extra Hours* (`hr_attendance_display_overtime`).
- `hide_on_dashboard` of the overtime time off types must be `False`, so the balances are shown on the time off dashboard.
- Reuse the existing time off type `hr_holidays.holiday_status_extra_hours` instead of creating a duplicate
  *Extra Hours* type.
- No hint text below the linked overtime rules on the time off type form.
- No page *Extra Hours and Overtime* on the employee form.
- The extra hours rule must have a maximum of hours per week: 45 h weekly limit minus the 38 h contract
  is 7 h per week. Hours above the limit must not be lost, they stay on the overtime rule.
- The module name is *HR Holidays Attendance Overtime* (not *Hr*).
- Data records must be updatable, no `noupdate="1"`, because the ruleset can be archived.
- Demo data is required in a `demo/` folder registered in the manifest.
- The ruleset name must be translatable.
- `hr.attedance:overtime_hours` and `hr.attedance:validated_overtime_hours` are extra hours in this context
- Calculate the overtime (Überzeit) in an new field `hr.attedance:weekly_overtime_hours` in the last entry of the week

Here is an example for 38 h contact, working 11h a day for an entire week:

| Weekday   | Date   | Hours | Type        |
| --------- | ------ | ----- | ----------- |
| Monday    | Nov 16 | 3.4 h | Überstunden |
| Tuesday   | Nov 17 | 3.4 h | Überstunden |
| Wednesday | Nov 18 | 0.2 h | Überstunden |
| Thursday  | Nov 19 | —     | Überstunden |
| Friday    | Nov 20 | —     | Überstunden |
| Friday    | Nov 20 | 10 h  | Überzeit    |

### Testing

Setup tests for check if the link between the new overtime rule and leave type works. Do not test other functionalities.

Prepare the local environment so I can run manual tests.

@Clanker When task is completed set frontmatter state to review. If you have access to session info add token count and session id. Prompt the author to verify the results.

## Worklog

### Implementation

Re-implemented `smartme_overtime_split` as `hr_holidays_attendance_overtime` (Odoo 19.0).

**Models** (bootstrapped with `task generate-module-inherit-model`):

- `models/hr_attendance_overtime_ruleset.py`: makes the ruleset `name` translatable, adds the `employee_count`
  smart button field and `action_open_employees()`.
- `models/hr_attendance_overtime_rule.py`: `leave_type_id` on `hr.attendance.overtime.rule` plus a constraint that the
  time off type has `overtime_deductible` enabled and does not require an allocation.
- `models/hr_attendance_overtime_line.py`: stored `overtime_leave_type_id` computed from the deciding rule
  (highest sequence wins) via `_get_deciding_rule()`.
- `models/hr_leave_type.py`: `overtime_rule_ids`, `_is_linked_overtime_type()`, display name with available hours
  and one dashboard tile per linked time off type.
- `models/hr_employee.py`: `_get_overtime_leave_type_balances()`.
- `models/hr_leave.py`: `_check_overtime_deductible()` checks the balance of the linked time off type.

All user-facing strings are English and translated in `i18n/de.po`. All methods have docstrings.

**Views** (bootstrapped with `task generate-module-inherit-view` / `generate-module-views`), one file per model:

- `views/hr_attendance_overtime_ruleset.xml`: smart button with the number of employees using the ruleset.
- `views/hr_attendance_overtime_rule.xml`: time off type and weekly limit on the overtime rule.
- `views/hr_leave_type.xml`: linked overtime rules on the time off type.
- `views/hr_attendance.xml`: time off type column in the overtime lines of an attendance, the weekly
  overtime field on the form, in the attendance list (optional column) and in
  `hr_attendance.view_attendance_tree_management`.
- `views/hr_attendance_overtime_line.xml`: report list, pivot, search, action and menu
  (*Attendances > Reporting > Extra Hours and Overtime*).

**Data** (updatable):

- `data/hr_leave_type.xml`: shows the existing `hr_holidays.holiday_status_extra_hours` type on the dashboard and
  creates the "Overtime" type (hour unit, overtime deductible, no allocation).
- `data/hr_attendance_overtime_ruleset.xml`: ruleset "Extra Hours and Overtime" with
  rule "Extra Hours" (quantity, day, hours from contract, max 7 h/week, sequence 10) and
  rule "Overtime" (quantity, week, 45 h, sequence 20).

**Hook** `hooks.py`: the `post_init_hook` enables *Display Extra Hours* (`hr_attendance_display_overtime`)
on all companies, so the overtime balances are visible after the installation.

**Demo data** `demo/hr_attendance_demo.xml` (loaded with the demo data of the database):
attendances of the current week for *Mitchell Admin* (5 x 12 h) and the ruleset on his contract.

**Weekly limit** `max_extra_hours` on the rule is the maximum of worked hours per week (45 h).
The extra hours are the difference between this limit and the contract of the employee
(`_get_max_extra_hours_for_employee`, based on `_get_expected_hours_from_contract`), e.g. 7 h for a
38 h contract and 25 h for a 20 h contract.

`_generate_overtime_vals_v2` generates the rules linked to a time off type separately and concatenates
the vals. The core merges the intervals of all rules and splits the overlaps, so that the same hours
are credited to only one rule. A daily rule with a weekly limit and a weekly rule credit different
hours by design (up to the limit and above the limit), the merge would drop the hours of one of them.
`_apply_max_extra_hours` then caps the hours of the capped rule per week, the excess is removed from
the last days of the week.

**Attendance fields** `hr.attendance.overtime_hours` and `hr.attendance.validated_overtime_hours` are
overridden to count only the extra hours. The hours of rules with a weekly period are weekly overtime
(*Überzeit*), they are shown in the new field `hr.attendance.weekly_overtime_hours` on the last
attendance of the week.

**Tests** `tests/test_overtime_leave_type.py` (9 tests):
link on both models, line gets the type of its rule, highest sequence decides, balance per type,
invalid time off type raises a `ValidationError`, weekly limit caps the extra hours, no limit credits
all hours, extra hours and overtime do not overlap (7 h + 10 h = 17 h for 55 h worked and a 38 h contract),
weekly overtime is shown on the last attendance of the week only.

### Verification

- `task translate-module addons/hr/hr_holidays_attendance_overtime` generated `i18n/de.po`, translations completed
  ("Extra Hours" → "Überstunden", "Overtime" → "Überzeit").
- `pre-commit` in `addons/hr` passes (ruff, pylint-odoo, oca-checks, prettier).
- Module installed on database `19.0`, tests: `0 failed, 0 error(s) of 9 tests`.
- `task generate-module-docs` / `task docs` regenerate `README.rst`, `static/description/index.html` and `README.md`.

### Manual test setup

The module is installed on the local database `19.0` (German `de_CH` active).
The ruleset *Extra Hours and Overtime* is assigned to the employees *Mitchell Admin* and *Marc Demo*.

The demo data `demo/hr_attendance_demo.xml` creates attendances of the current week for
*Mitchell Admin* (5 x 12 h = 60 h, contract is 38 h/week) and assigns the ruleset to his contract.
They trigger both rules:

| Weekday   | Date   | Hours | Type        |
| --------- | ------ | ----- | ----------- |
| Monday    | Nov 16 | 3.4 h | Überstunden |
| Tuesday   | Nov 17 | 3.4 h | Überstunden |
| Wednesday | Nov 18 | 0.2 h | Überstunden |
| Thursday  | Nov 19 | —     | Überstunden |
| Friday    | Nov 20 | —     | Überstunden |
| Friday    | Nov 20 | 10 h  | Überzeit    |

Balances: *Überstunden* 7:00 h, *Überzeit* 10:00 h. The extra hours are capped to the 7 h between the
45 h weekly limit and the 38 h contract, the weekly rule credits the 10 h above the 45 h limit.

The attendance fields show the split per day:

| Date   | Worked | `overtime_hours` | `validated_overtime_hours` | `weekly_overtime_hours` |
| ------ | ------ | ---------------- | -------------------------- | ----------------------- |
| Nov 16 | 11 h   | 3.4 h            | 3.4 h                      | —                       |
| Nov 17 | 11 h   | 3.4 h            | 3.4 h                      | —                       |
| Nov 18 | 11 h   | 0.2 h            | 0.2 h                      | —                       |
| Nov 19 | 11 h   | —                | —                          | —                       |
| Nov 20 | 11 h   | —                | —                          | 10 h                    |

The weekly overtime is only shown on the last attendance of the week, the extra hours fields never
contain it.
The sum of the lines is the hours above the contract (55 h worked - 38 h contract = 17 h).

Manual test steps:

1. Start Odoo: `./task start source 19.0` and open <http://localhost:8069/web?debug=1&db=19.0>.
2. Open *Attendances > Configuration > Overtime Rulesets > Extra Hours and Overtime* and check both rules and their
   time off type.
3. Check *Attendances > Reporting > Extra Hours and Overtime* for the demo attendances of *Mitchell Admin*.
4. Open *Time Off > Dashboard* and check the tiles *Überstunden* and *Überzeit* of *Mitchell Admin*.
5. Request hours of the type *Überzeit* and check that the balance is reduced.

@Clanker: please verify the results. Confirm to set the state to `completed`, otherwise it is set to `aborted`.
