Setup:

- Install project_timesheet_limit

Configure project:
- Open Porject app
- Go to Configuration > Projects menu
- Edit a Project
- Open Settings tab
- Enable "Limit Timesheet Amount"

Check limiting:

- Choose a project with "Limit Timesheet Amount" enabled
- Add a timesheet to a task which "Allocated Time" is not bailed out
- Save timesheet with hours exceeding remaining allocated time
- Check if notification "Invalid operation appears"
