---
commit_ref: 54fcd7795638563a54ec3ca0ba70bbc1486c4375
title: "hr_timesheet_attendance_report_billable_add_kulanz"
author: "laurens kooijman <laurenskooijman@gmail.com>"
session_id: 01a2074f-b514-7158-aa42-2b0e8138eb0a
action: execute
state: completed
date_completed: 2026-11-23
harness: pi
provider: moonshotai
model: Kimi-K2.6
input_tokens: 22936
output_tokens: 7253
---

# hr_timesheet_attendance_report_billable_add_kulanz

Note: @Clanker refers to the "ai agent" (you) who is working on this prompt file.

@Clanker when working on this prompt file, make sure to:

- Read the `AGENTS.md` to get an understanding of the project
- Read task section and prepare a list of todos
- Update the todo list while working on task

## Task

To the report in `hr_timesheet_attendance_report_billable` add the fields `courtesy` and `courtesy_ratio`.
The basis for timesheet hours to be counted in the `courtesy` field, use the field `default_code` on the `product` in the `sale order line`. If this is equal to 'KUL', count it as courtesy hours. 

Subtract the courtesy hours from the hours in non_billable_timesheet.

Add to the method `read_group` the `courtesy` in the same way as the other 3 fields are present.

Shorten the field strings like this, but keep the field names as they are:

"Billable Timesheet Hours" -> "Billable"
"Non-Billable Timesheet Hours" -> "Non-Billable"
"Internal Timesheet Hours" -> "Internal"
"Billable Timesheet Ratio" -> "Billable %"
"Non-Billable Timesheet Ratio" -> "Non-Billable %"
"Internal Timesheet Ratio" -> "Internal %"

New field `courtesy`: "Courtesy"
New field `courtesy_ratio`: "Courtesy %"

Add Translations:

"Billable"  -> "Abrechenbar"
"Non-Billable" -> "Abrechenbar"
"Internal" -> "Intern"
"Courtesy" -> "Kulanz"
"Billable %" -> "Abrechenbar %"
"Non-Billable %" -> "Abrechenbar %"
"Internal %" -> "Intern %"
"Courtesy %" -> "Kulanz %"


@Clanker When task is completed set frontmatter state to review. If you have access to session info add token count and session id. Prompt the author to verify the results.

## Worklog

- Added `courtesy` and `courtesy_ratio` fields to `hr.timesheet.attendance.report`.
- Updated SQL view to detect courtesy hours via `sale_order_line` -> `product_product.default_code = 'KUL'`. Courtesy hours are excluded from `non_billable_timesheet`.
- Added `courtesy` and `courtesy_ratio` to the pivot view.
- Shortened field labels for existing billable/non-billable/internal fields and their ratios.
- Updated German translations (`de.po`) for all shortened labels and new courtesy fields.
- Verified Python and XML syntax.

## Changelog

- `report/hr_timesheet_attendance_report.py`:
  - Shortened field labels for `billable_timesheet`, `non_billable_timesheet`, `internal_timesheet`, and their ratio counterparts.
  - Added `courtesy` and `courtesy_ratio` Float fields with `group_operator='avg'`.
  - Extended the SQL view to join `sale_order_line` and `product_product` to identify courtesy hours when `default_code = 'KUL'`.
  - Courtesy hours are now excluded from `non_billable_timesheet` and tracked separately.
  - Added `courtesy_ratio` computation in the outer SQL query.
  - Updated `read_group` to recalculate `courtesy_ratio:avg` aggregated values from total timesheet.

- `report/hr_timesheet_attendance_report_view.xml`:
  - Added `courtesy` (measure, `timesheet_uom` widget) and `courtesy_ratio` (measure, `percentage` widget) to the pivot view.

- `i18n/de.po`:
  - Updated translations for shortened field labels.
  - Added translations for `Courtesy` / `Kulanz` and `Courtesy %` / `Kulanz %`.
