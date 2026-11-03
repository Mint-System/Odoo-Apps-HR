---
commit_ref: 64b2befb92e9c287beb42d9127e71496006d300a
title: "hr-timesheet-attendance-record-allow-date-employee-changes"
author: "laurens kooijman <laurenskooijman@gmail.com>"
action: implement
state: completed
date_completed: 2026-11-03
harness: pi
provider: moonshotai
model: moonshotai/Kimi-K2.6
input_tokens: 34819
output_tokens: 9842
---

# hr-timesheet-attendance-record-allow-date-employee-changes

Note: @Clanker refers to the "ai agent" (you) who is working on this prompt file.

@Clanker when working on this prompt file, make sure to:

- Read the `AGENTS.md` and `README.md` to get an understanding of the project
- Read entire task section and prepare a list of todos
- Update the todo list while working on task

## Task

With this prompt (tmp/prompt-log/2026-09-15_new-module-hr-timesheet-attendance-record.md) a module was created and then adjusted manually to fullfill the criteria. Read the prompt to know the context.

Add these steps to the write function when either of the fields `date` and `employee_id` are changed.
- If there is only one timesheet in the connected attendance, unlink the attendance.
- Otherwise, Remove the timesheet id from the linked attendance (the `timesheet_ids` field) and Execute `_update_overtime()` on this attendance.
- Find the attendance on the date and employee_id after the change has been made on the timesheet entry
- If the attendance exists, link it with the timesheet entry through the one2many/many2one field.
- If the attendance does not exist, create it in the same way as it is created in the create method.
- Execute `_update_overtime()` on the newly linked/created attendance.


@Clanker When task is completed set frontmatter state to review. Prompt the author to verify the results.

## Worklog

- Read existing module code in `addons/hr/hr_timesheet_attendance_record/models/account_analytic_line.py` and `hr_attendance.py`.
- Extended the `write()` method on `AccountAnalyticLine` (`account_analytic_line.py`) to handle `date` and `employee_id` changes:
  - Store `current_attendance` before calling `super().write(vals)`.
  - If `date` or `employee_id` changed:
    - Check whether the old attendance only contains this timesheet (`len(current_attendance.timesheet_ids) == 1`).
    - Clear the timesheet's `attendance_id` via `super(AccountAnalyticLine, self).write({'attendance_id': False})` to avoid `ondelete="restrict"` issues.
    - Unlink the old attendance if it only had this timesheet; otherwise call `_update_overtime()` on it.
    - Find or create a new attendance for the updated `date`/`employee_id` and link it.
    - Call `_update_overtime()` on the newly linked/created attendance.
- Verified Python syntax compiles correctly.

@Clanker If author confirms results set frontmatter state to completed, otherwise to aborted. Update date, harness, provider and model. If you have access to session info also add token count.
