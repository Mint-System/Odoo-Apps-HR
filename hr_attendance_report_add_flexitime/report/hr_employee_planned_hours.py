# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, time

class HREmployeePlannedHours(models.Model):
    _name = "hr.employee.planned.hours"
    _description = "Planned Work Hours per Employee per Day"
    _order = "date desc, employee_id"
    _auto=True

    employee_id = fields.Many2one('hr.employee', required=True, index=True)
    date = fields.Date(required=True, index=True)
    planned_hours = fields.Float("Planned Hours", digits=(16, 2))

    _sql_constraints = [
        ('unique_employee_date', 'unique(employee_id, date)', 'Only one record per employee and date!')
    ]


    @api.model
    def _to_date(self, val):
        if not val:
            return None
        if isinstance(val, str):
            return fields.Date.from_string(val)
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val
        raise ValueError(f"Invalid date format: {val!r}")

    
    @api.model
    def compute_planned_hours(self, date_from=None, date_to=None):
        """Rebuild table of planned hours between given dates (or all if none)."""
        date_from = self._to_date(date_from)
        date_to = self._to_date(date_to)

        yesterday = fields.Date.to_string(fields.Date.subtract(fields.Date.today(), days=1))

        Employee = self.env['hr.employee']
        self.env.cr.execute("DELETE FROM hr_employee_planned_hours") 

        employees = Employee.search([])
        for employee in employees:
            calendar = employee.resource_calendar_id
            if not calendar:
                continue
            # date range
            # start = date_from or fields.Date.today().replace(day=1)
            # end = date_to or fields.Date.today()
            start = date_from or yesterday
            end = date_to or yesterday
            current = start
            while current <= end:
                min_dt = datetime.combine(current, time.min)
                max_dt = datetime.combine(current, time.max)
                planned = calendar.get_work_hours_count(min_dt, max_dt, True)
                if planned:
                    self.create({
                        'employee_id': employee.id,
                        'date': current,
                        'planned_hours': planned,
                    })
                current = fields.Date.add(current, days=1)
