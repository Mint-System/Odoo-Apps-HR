---
commit_ref: 3e5e219b7d4cb27916722199c1755c2302e78a05
title: "add permission to hr_timesheet_attendance_report_billable"
author: "laurens kooijman <laurenskooijman@gmail.com>"
action: implement
state: completed
date_completed: 2026-11-12
harness: pi
provider: infomaniak
model: moonshotai/Kimi-K2.6
input_tokens: 3115
output_tokens: 1430
---

# add permission to hr_timesheet_attendance_report_billable

Note: @Clanker refers to the "ai agent" (you) who is working on this prompt file.

@Clanker when working on this prompt file, make sure to:

- Read the `AGENTS.md` and `README.md` to get an understanding of the project
- Read entire task section and prepare a list of todos
- Update the todo list while working on task

## Task

In the module `hr_timesheet_attendance_report_billable` (addons/hr/hr_timesheet_attendance_report_billable) I want you to add the menu item `hr_timesheet.menu_timesheets_reports` to the group `hr_timesheet.group_hr_timesheet_user`.

@Clanker When task is completed set frontmatter state to review. Prompt the author to verify the results.

## Worklog

Added an `<record>` element in `report/hr_timesheet_attendance_report_view.xml` that updates the `groups_id` field of `hr_timesheet.menu_timesheets_reports` to include `hr_timesheet.group_hr_timesheet_user` via `[(4, ref('hr_timesheet.group_hr_timesheet_user'))]`. This grants regular timesheet users access to the Reporting menu alongside the existing approver group.

@Clanker If author confirms results set frontmatter state to completed, otherwise to aborted. Update date, harness, provider and model. If you have access to session info also add token count.
