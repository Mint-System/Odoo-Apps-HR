---
title: "New Module HR Timesheet Attendance Record"
state: draft
model: 
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

#### Fields

Link the two models account.analytic.line and hr.attendance together with these two fields, which hold the attached entries.
- account.analytic.line:attendance_id (many2one)
- hr.attendance:timesheet_ids (one2many)

Change the field hr.attendance:check_out to an computed field which depends on "timesheet_ids.unit_amount". In the compute method, set the value of check_out to `check_in + sum(timesheet_ids.mapped("unit_amount")`.

Add readonly = False to the field hr.attendance:check_out.

#### Methods

In account.analytic.line create these methods:

account.analytic.line:_get_attendance_record
Variables: date, employee_id

Look for attendances from employee_id and on date.

For all attendances, unlink those that do not have the field timesheet_ids set, keep the first attendance with the field timesheet_ids set and unlink if any following attendance has the field timesheet_ids set.

Return the kept attendance or False.


account.analytic.line:_create_attendance
Variables: date, employee_id

Create an attendance with employee_id = employee_id, check_in = 8:00 on date.

Return the attendance that is created.


account.analytic.line:create
Variables: vals_list

First get the attendance on the day of this timesheet entry (vals_list["date"]) and from the employee (vals_list["employee_id"] with the method _get_attendance_record.

If an attendance is found, append it to the vals_list (vals_list["attendance_id"]), otherwise create the attendance with _create_attendance

Use this snippet:

```
def create(self, vals_list): 
	attendance = self._get_attendance_record(vals_list["date"], vals_list["employee.id"])
	if attendance
		vals_list["attendance_id"] = attendance
	else
		vals_list["attendance_id"] = self._create_attendance
	return super().create(vals_list)
```

account.analytic.line:unlink

If the field timesheet_ids in record.attendance_id has length 1, unlink the attendance entry. Then run the the super().unlink() method.


### Views

Use this task command to create the views

```bash
task generate-module-views addons/hr/hr_timesheet_attendance_recording hr.attendance
```

In the form view of hr.attendance add a smart-button that shows the amount of linked timesheet entries (account.analytic.line) and when clicked shows these timesheet entries in a list.


### Test instructions

Write in tests/TEST_INSTRUCTIONS.rst what steps need to be taken to see if and how this model works. Keep it very simple and limit to single sentences, such as 'create a timesheet entry for 1 hour' and 'check the duration of the attendance created'.


### Testing

I will test the module myself so do not run "task all" and "task lint".


## Worklog

@Clanker Add a summary here once the task has been completed.

@Clanker Set frontmatter state to completed and update info about model and token usage.