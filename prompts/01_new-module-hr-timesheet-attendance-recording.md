---
title: "New Module HR Timesheet Attendance Recording"
state: completed
model: infomaniak/moonshotai/Kimi-K2.6
input_tokens: ~15000
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

It is your task to create a new Odoo module. The module has been initialized and can be found in "addons/hr/hr_timesheet_attendance_recording".

The goal is to create Attendance records for each timesheet entry that is made or edited.


### Models

Use these task commands to generate the model files:

``` bash
task generate-module-model addons/hr/hr_timesheet_attendance_recording hr.attendance
task generate-module-model addons/hr/hr_timesheet_attendance_recording account.analytic.line
```

#### Fields

Link the two models account.analytic.line and hr.attendance together with these two fields, which hold the attached entries.
- account.analytic.line:attendance_id (many2one)
- hr.attendance:timesheet_ids (one2many)

Change the field hr.attendance:check_out to an computed field which depends on timesheet_ids, where the compute method sets the value to "check_in + sum(timesheet_ids.mapped("unit_amount")". If there are no timesheet_ids, set the field to False to keep the default behaviour.

#### Methods

In account.analytic.line add features for these methods:

account.analytic.line:create
Look for attendances from the same employee on the same date as the currently created entry.
From these attendances, unlink any attendances without the check_out field set and check_in is after 8:00. Keep the entry where the field timesheet_ids is set, in a variable.
If this variable is False (i.e. no record found), create a new Attendance Entry that starts at 8:00 and with timesheet_ids = the id of the currently created entry.
Store in this entry, the attendance id that is created or appended to in the field attendance_id.

account.analytic.line:unlink
If the field timesheet_ids in the attendance linked to this entry (field attendance_id) has length 1, unlink the attendance entry. Otherwise remove the id of this entry from the attendance:timesheet_ids.

account.analytic.line:write
If the unit_amount is changed of this entry, trigger the compute check_out method in the linked attendance after the value is written in this entry.

### Views

Use this task command to create the views

``` bash
task generate-module-views addons/hr/hr_timesheet_attendance_recording hr.attendance
```

In the form view of hr.attendance add a smart-button that shows the amount of linked timesheet entries (account.analytic.line) and when clicked shows these timesheet entries in a list.

### Test instructions

Write in tests/TEST_INSTRUCTIONS.rst what steps need to be taken to see if and how this model works. Keep it very simple and limit to single sentences, such as 'create a timesheet entry for 1 hour' and 'check the duration of the attendance created'.

### Testing

I will test the module myself.


## Worklog

- Updated `__manifest__.py` with dependencies `hr_timesheet` and `hr_attendance`.
- Generated model stubs for `hr.attendance` and `account.analytic.line`.
- Extended `hr.attendance` with `timesheet_ids` (One2many) and `timesheet_count` (computed Integer).
- Overrode `hr.attendance.check_out` to be a computed field based on `check_in + sum(timesheet_ids.unit_amount)`; resets to `False` when no timesheets are linked.
- Extended `account.analytic.line` with `attendance_id` (Many2one).
- Implemented `create`, `unlink`, and `write` methods on `account.analytic.line` per specification.
- Generated inherited form view for `hr.attendance` adding a smart-button that shows linked timesheet count and opens them in a list.
- Wrote `tests/TEST_INSTRUCTIONS.rst` with simple manual test steps.
- Ran pre-commit linting without errors.
