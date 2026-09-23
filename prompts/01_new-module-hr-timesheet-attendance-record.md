---
title: "New Module HR Timesheet Attendance Record"
state: completed
model: infomaniak/moonshotai/Kimi-K2.6
input_tokens: 
---

# Run 01

Note: @Clanker refers to the "ai agent" (you) who is working on this task.

@Clanker when working on this task, make sure to:

- Read context and task section first
- Prepare a list of todos
- Update the todo list while working on the task

## Context

@Clanker Read the `AGENTS.md` and `README.md` to get an understanding of the project.

## Task

The goal for this task is to create a new Odoo module with the description written below. The module has already been initialized. This code can be found in "addons/hr/hr_timesheet_attendance_record".

### Models

Use these task commands to generate the necessary models:

``` bash
task generate-module-model addons/hr/hr_timesheet_attendance_recording hr.attendance
task generate-module-model addons/hr/hr_timesheet_attendance_recording account.analytic.line
```

### Fields

Link the two models `account.analytic.line` and `hr.attendance` together with these two fields, which hold the attached entries:

- `account.analytic.line:attendance_id` many2one
- `hr.attendance:timesheet_ids` one2many

Change the field `hr.attendance:check_out` to an computed field which depends on `"timesheet_ids.unit_amount"`. In the compute method, set the value of check_out to `check_in + sum(timesheet_ids.mapped("unit_amount")`.

Add `readonly=False` to the field `hr.attendance:check_out`.

### Methods

In `account.analytic.line` create these methods:

`account.analytic.line:_get_attendance_record(date, employee_id)`

Look for attendances from `employee_id` and on `date`. Return attendance_id or False. If found more than one attendance raise an validation error.

`account.analytic.line:_create_attendance(date, employee_id)`

Creates an attendance with employee_id = employee_id, check_in = 8:00 on date. Returns the attendance that is created.

`account.analytic.line:create(vals_list)`

First get the attendance on the day of this timesheet entry `vals_list["date"]` and from the employee `vals_list["employee_id"]` with the method `_get_attendance_record`.

If an attendance is found, link it in the `vals_list["attendance_id"])`, otherwise create the attendance with `_create_attendance`.

```python
def create(self, vals_list): 
	for val in vals_list:
		attendance = self._get_attendance_record(val["date"], val["employee.id"])
		if attendance
			val["attendance_id"] = attendance
		else
			val["attendance_id"] = self._create_attendance
	return super().create(vals_list)
```

`account.analytic.line:unlink`

If the field `timesheet_ids` has length 1, unlink the attendance entry.

### Views

Use this task command to create the views:

```bash
task generate-module-views addons/hr/hr_timesheet_attendance_recording hr.attendance
```

In the form view of `hr.attendance` add a smart-button that shows the amount of linked timesheet entries (`account.analytic.line`) and when clicked shows these timesheet entries in a list.

### Test instructions

Write in `tests/TEST_INSTRUCTIONS.rst` what steps need to be taken to see if and how this model works. Keep it very simple and limit to single sentences, such as 'create a timesheet entry for 1 hour' and 'check the duration of the attendance created'.

### Testing

I will test the module myself so do not run "task all" and "task lint".

## Worklog

- Created `models/account_analytic_line.py` with `attendance_id` field, `_get_attendance_record`, `_create_attendance`, `create`, and `unlink` overrides.
- Created `models/hr_attendance.py` with `timesheet_ids` field and computed `check_out` depending on `timesheet_ids.unit_amount`.
- Added `views/hr_attendance.xml` with a smart-button on the attendance form showing the number of linked timesheets.
- Updated `__manifest__.py` to reference the new view and `models/__init__.py` to import both models.
- Wrote `tests/TEST_INSTRUCTIONS.rst` with manual test steps.