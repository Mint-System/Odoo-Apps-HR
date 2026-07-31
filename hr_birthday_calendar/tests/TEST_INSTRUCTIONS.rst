Setup Employees:

- Login as admin.
- Open Settings > Users & Companies > Groups
- Search for Employees groups
- Remove Marc Demo from groups "Employees/Administrator" and "Employees/Officer : Manage all employees"
- Go to Employees and edit Marc Demo 
- In tab "Private Information" set birthday to value with actual month

Setup Action and Menu:

- Go to Settings > Technical > Window Actions
- Create new action with 
  - name = "Birthdays"
  - object = "hr.employee.public"
  - action type = "ir.actions.act_window"
  - view mode = "calendar"
- Go to Settings > Technical > Menu Items
- Create new Menu item with
  - menu = "Birthdays"
  - parent menu = "Employees"
  - actio = "ir.actions.act_window Birthdays"

Birthday Calendar:

- Login as Marc Demo (demo/demo)
- Go to Employees > Directory
- Edit Mar Demo
- Confirm birthday entry
- Switch to calendar view
- Confirm Marc Demo's birthday is shown

Direct access:

- Go to Employees > Birthdays
- Calendar view with birthday is shown

