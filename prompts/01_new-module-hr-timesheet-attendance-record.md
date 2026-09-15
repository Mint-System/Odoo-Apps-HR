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

Change the field hr.attendance:check_out to an computed field which depends on "timesheet_ids.unit_amount". In the compute method, set the value of check_out to "check_in + sum(timesheet_ids.mapped("unit_amount")". 

Add readonly = False to the field hr.attendance:check_out.

#### Methods

In account.analytic.line create these methods:

account.analytic.line:_create_attendance
Variables: date, employee_id, record_id

Create an attendance with employee_id = employee_id, check_in = 8:00 on date in the employee's timezone, timesheet_ids = record_id.

Return the attendance_id that is created


account.analytic.line:_append_timesheet_id
Variables: attendance, timesheet_id

For the given attendance, append timesheet_id to the field timesheet_ids


account.analytic.line:_remove_timesheet_id
Variables: attendance, timesheet_id

For the given attendance, remove timesheet_id from the field timesheet_ids


account.analytic.line:_sync_attendance
Variables: date, employee_id, record_id

Look for attendances from employee_id and on date.

For all attendances, unlink those that do not have the field timesheet_ids set, keep the first attendance with the field timesheet_ids set and unlink if any following attendance has the field timesheet_ids set.

If an attendance is kept from the previous step, call _append_timesheet_id with this attendance and record_id, otherwise call _create_attendance with date, employee_id and record_id.

Return the attendance_id that is either found or created.


account.analytic.line:create
Variables: vals_list

Create the timesheet entries by vals_list.

For each created entry, run _sync_attendance with record.date, record.employee_id and record.id. Store in this entry the attendance_id that is returned by _sync_attendance into the field attendance_id


account.analytic.line:unlink

If the field timesheet_ids in record.attendance_id has length 1, unlink the attendance entry. Otherwise run _remove_timesheet_id with record.attendance_id and record.id.


account.analytic.line:write
Variables: vals

After the values are written for this entry, if unit_amount is in vals, trigger the compute check_out method in record.attendance_id 


### Views

Use this task command to create the views

``` bash
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