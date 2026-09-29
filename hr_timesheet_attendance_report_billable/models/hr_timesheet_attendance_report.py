# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models, tools

_logger = logging.getLogger(__name__)


class HrTimesheetAttendanceReport(models.Model):
    _inherit = "hr.timesheet.attendance.report"

    billable_timesheet = fields.Float("Billable Timesheet Hours", readonly=True)
    non_billable_timesheet = fields.Float("Non-Billable Timesheet Hours", readonly=True)
    internal_timesheet = fields.Float("Internal Timesheet Hours", readonly=True)
    billable_timesheet_ratio = fields.Float("Billable Timesheet Ratio", readonly=True, group_operator='avg')
    non_billable_timesheet_ratio = fields.Float("Non-Billable Timesheet Ratio", readonly=True, group_operator='avg')
    internal_timesheet_ratio = fields.Float("Internal Timesheet Ratio", readonly=True, group_operator='avg')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    max(id) AS id,
                    t.employee_id,
                    t.date,
                    t.company_id,
                    coalesce(sum(t.attendance), 0) AS total_attendance,
                    coalesce(sum(t.timesheet), 0) AS total_timesheet,
                    coalesce(sum(t.attendance), 0) - coalesce(sum(t.timesheet), 0) AS total_difference,
                    NULLIF(sum(t.timesheet) * t.emp_cost, 0) AS timesheets_cost,
                    NULLIF(sum(t.attendance) * t.emp_cost, 0) AS attendance_cost,
                    NULLIF((coalesce(sum(t.attendance), 0) - coalesce(sum(t.timesheet), 0)) * t.emp_cost, 0) AS cost_difference,
                    coalesce(sum(t.billable_timesheet), 0) AS billable_timesheet,
                    coalesce(sum(t.non_billable_timesheet), 0) AS non_billable_timesheet,
                    coalesce(sum(t.internal_timesheet), 0) AS internal_timesheet,
                    CASE WHEN coalesce(sum(t.timesheet), 0) != 0 THEN coalesce(sum(t.billable_timesheet), 0) / coalesce(sum(t.timesheet), 0) ELSE 0 END AS billable_timesheet_ratio,
                    CASE WHEN coalesce(sum(t.timesheet), 0) != 0 THEN coalesce(sum(t.non_billable_timesheet), 0) / coalesce(sum(t.timesheet), 0) ELSE 0 END AS non_billable_timesheet_ratio,
                    CASE WHEN coalesce(sum(t.timesheet), 0) != 0 THEN coalesce(sum(t.internal_timesheet), 0) / coalesce(sum(t.timesheet), 0) ELSE 0 END AS internal_timesheet_ratio
                FROM (
                    SELECT
                        -hr_attendance.id AS id,
                        hr_employee.hourly_cost AS emp_cost,
                        hr_attendance.employee_id AS employee_id,
                        hr_attendance.worked_hours AS attendance,
                        NULL AS timesheet,
                        CAST(hr_attendance.check_in
                                at time zone 'utc'
                                at time zone
                                    (SELECT calendar.tz FROM resource_calendar as calendar
                                    INNER JOIN hr_employee as employee ON employee.id = hr_attendance.employee_id
                                    WHERE calendar.id = employee.resource_calendar_id)
                        as DATE) as date,
                        hr_employee.company_id as company_id,
                        NULL AS billable_timesheet,
                        NULL AS non_billable_timesheet,
                        NULL AS internal_timesheet
                    FROM hr_attendance
                    LEFT JOIN hr_employee ON hr_employee.id = hr_attendance.employee_id
                UNION ALL
                    SELECT
                        ts.id AS id,
                        hr_employee.hourly_cost AS emp_cost,
                        ts.employee_id AS employee_id,
                        NULL AS attendance,
                        ts.unit_amount AS timesheet,
                        ts.date AS date,
                        ts.company_id AS company_id,
                        CASE WHEN ts.so_line IS NOT NULL AND ts.timesheet_invoice_type != 'non_billable' THEN ts.unit_amount ELSE 0 END AS billable_timesheet,
                        CASE WHEN ts.so_line IS NOT NULL AND ts.timesheet_invoice_type = 'non_billable' THEN ts.unit_amount ELSE 0 END AS non_billable_timesheet,
                        CASE WHEN ts.so_line IS NULL THEN ts.unit_amount ELSE 0 END AS internal_timesheet
                    FROM account_analytic_line AS ts
                    LEFT JOIN hr_employee ON hr_employee.id = ts.employee_id
                    WHERE ts.project_id IS NOT NULL
                ) AS t
                GROUP BY t.employee_id, t.date, t.company_id, t.emp_cost
                ORDER BY t.date
            )
        """
            % self._table
        )
