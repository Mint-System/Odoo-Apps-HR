# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo import tools


class HRAttendanceLeaveReport(models.Model):
    _name = "hr.attendance.leave.report"
    _description = "Attendance and Leave Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    employee_id = fields.Many2one('hr.employee', 'Employee', readonly=True)
    department_id = fields.Many2one('hr.department', 'Department', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    date = fields.Date('Date', readonly=True)
    worked_hours = fields.Float('Worked Hours', readonly=True)
    attendance_count = fields.Integer('Attendance Records', readonly=True)
    leave_hours_vacation = fields.Float("Vacation Hours", readonly=True)
    leave_hours_sick = fields.Float("Sick Leave Hours", readonly=True)
    total_leave_hours = fields.Float("Total Leave Hours", readonly=True)

    def _select(self):
        return """
            SELECT
                CONCAT('att_', MIN(hra.id)) as id,
                hra.employee_id,
                he.department_id,
                he.company_id,
                CAST(hra.check_in AS DATE) as date,
                SUM(hra.worked_hours) as worked_hours,
                COUNT(hra.id) as attendance_count,
                0 as leave_hours_vacation,
                0 as leave_hours_sick,
                0 as total_leave_hours
            FROM hr_attendance hra
            INNER JOIN hr_employee he ON he.id = hra.employee_id
            GROUP BY hra.employee_id, CAST(hra.check_in AS DATE), he.department_id, he.company_id

            UNION ALL

            SELECT
                CONCAT('leave_', hl.id, '_', gen_series.check_date) as id,
                hl.employee_id,
                he.department_id,
                he.company_id,
                gen_series.check_date as date,
                0 as worked_hours,
                0 as attendance_count,
                CASE WHEN hlt.code = 'FER' THEN 
                    (hl.number_of_days * 8.0 / (DATE_PART('day', hl.request_date_to::timestamp - hl.request_date_from::timestamp) + 1)) 
                    ELSE 0 END as leave_hours_vacation,
                CASE WHEN hlt.code = 'KRA' THEN 
                    (hl.number_of_days * 8.0 / (DATE_PART('day', hl.request_date_to::timestamp - hl.request_date_from::timestamp) + 1)) 
                    ELSE 0 END as leave_hours_sick,
                (hl.number_of_days * 8.0 / (DATE_PART('day', hl.request_date_to::timestamp - hl.request_date_from::timestamp) + 1)) as total_leave_hours
            FROM (
                SELECT 
                    hl.*,
                    generate_series(hl.request_date_from::date, hl.request_date_to::date, '1 day'::interval)::date as check_date
                FROM hr_leave hl
                INNER JOIN hr_leave_type hlt ON hlt.id = hl.holiday_status_id
                WHERE hl.state = 'validate' AND hlt.code IN ('FER', 'KRA')
            ) AS gen_series
            INNER JOIN hr_leave hl ON hl.id = gen_series.id
            INNER JOIN hr_employee he ON he.id = hl.employee_id
            INNER JOIN hr_leave_type hlt ON hlt.id = hl.holiday_status_id
            WHERE (DATE_PART('day', hl.request_date_to::timestamp - hl.request_date_from::timestamp) + 1) > 0
        """

    @api.model
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (%s)
        """ % (self._table, self._select())
        self.env.cr.execute(query)