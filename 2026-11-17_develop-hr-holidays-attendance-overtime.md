---
commit_ref:
title: "Develop HR Holidays Attendance Overtime"
author: "Janik von Rotz <login@janikvonrotz.ch>"
session_id:
action: execute
state: draft
date_completed: YYYY-MM-DD
harness:
provider:
model:
input_tokens:
output_tokens:
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

### Testing

Setup tests for check if the link between the new overtime rule and leave type works. Do not test other functionalities.

Prepare the local environment so I can run manual tests.

@Clanker When task is completed set frontmatter state to review. If you have access to session info add token count and session id. Prompt the author to verify the results.

## Worklog

@Clanker Add a summary here once the task has been completed.

@Clanker If author confirms results set frontmatter state to completed, otherwise to aborted. Update date, harness, provider and model. If you have access to session info update token count. Finally, update the changelog with the most important changes.
