---
title: "Create HR Attendance Timesheet Billable"
state: draft
model: moonshotai/Kimi-K2.6
input_tokens: 
---

# Run 33

Note: @Clanker refers to the "ai agent" (you) who is working on this task.

@Clanker when working on this task, make sure to:

- Read context and task section first
- Prepare a list of todos
- Update the todo list while working on the task

## Context

@Clanker Read the `AGENTS.md` and `README.md` to get an understanding of the project.

## Task

The goal for this task is to create a new Odoo module with the description written below. The module has already been initialized. This code can be found in "addons/hr/hr_attendance_timesheet_billable".

### Models

The report extends the data model `project.task`.
Use these task command to generate the inheriting model:

``` bash
task generate-module-inherit-model addons/hr/hr_attendance_timesheet_billable project.task
```

The module extends the report data model `hr.timesheet.attendance.report`.
Use these task command to generate the inheriting model:

``` bash
task generate-module-inherit-model addons/hr/hr_attendance_timesheet_billable hr.timesheet.attendance.report
```

### Fields

Add a boolean field `not_billable` "Not Billable" to `project.task` model.

Add these fields to `hr.timesheet.attendance.report` report model:

- `hr.timesheet.attendance.report: billable_timesheet` Float 
- `hr.timesheet.attendance.report: non_billable_timesheet` Float
- `hr.timesheet.attendance.report: internal_timesheet` Float
- `hr.timesheet.attendance.report: invoiced_timesheet` Float

### Methods

In `hr.timesheet.attendance.report` override or inherit from `init` method to take into account the following calculations in sql query:
- `billable_timesheet` counts together the recorded timesheets of project tasks not flagged by 'not_billable'.
- `non_billable_timesheet` counts together the recorded timesheets of project tasks flagged by 'not_billable' and linked to a `sale.order.line` entry.
- `internal_timesheet` counts together the recorded timesheets of project tasks not linked to a `sale.order.line` entry.

### Views
These new values for `hr.timesheet.attendance.report` can be shown in report "Timesheets > Reporting > Timesheets".

Extend the report view `hr_timesheet_attendance.view_hr_timesheet_attendance_report_pivot`. Use this task to inherit from ths view:
`task generate-module-inherit-view addons/hr/hr_attendance_timesheet_billable hr_timesheet_attendance.view_hr_timesheet_attendance_report_pivot hr.timesheet.attendance.report`

### Test instructions

Write in `tests/TEST_INSTRUCTIONS.rst` what steps need to be taken to see if and how this model works. Keep it very simple and limit to single sentences, such as 'create a timesheet entry for 1 hour' and 'check the billable timesheets on the report'.

### Testing

I will test the module myself so do not run "task all" and "task lint".

## Worklog

@Clanker Add a summary here once the task has been completed.

@Clanker Set frontmatter state to completed and update info about model and token usage.


