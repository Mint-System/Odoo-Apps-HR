- Create a public holiday with a duration of 1 hour and set the time_type to 'attendance'
- Add an attendance on the day of the "1h-public holiday", the total expected hours (worked - overtime) should be one less than what is in the working schedule. 
- Create an Absence (eg holiday) with time allocation half-day or hours on the day of the "1h-public holiday". The calculated time off should be 1 day.

- Create a time off type with the name "Home Office" and time_type 'other'
- Create a contract for an employee and set state to 'open'
- Create an "home office" absence for this employee.
- Add an attendance to the day of the "home office" absence. The attendance hours should be in the worked hours and not all in overtime.