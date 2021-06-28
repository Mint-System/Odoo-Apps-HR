from odoo import fields, models, tools

class LeaveReportCalendar(models.Model):
    _inherit = "hr.leave.report.calendar"

    department_id = fields.Many2one('hr.department', readonly=True)
    holiday_status_id = fields.Many2one('hr.leave.type', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'hr_leave_report_calendar')

        self._cr.execute("""CREATE OR REPLACE VIEW hr_leave_report_calendar AS
        (SELECT 
            row_number() OVER() AS id,
            ce.name AS name,
            ce.start_datetime AS start_datetime,
            ce.stop_datetime AS stop_datetime,
            ce.event_tz AS tz,
            ce.duration AS duration,
            hl.employee_id AS employee_id,
            em.company_id AS company_id,
            em.department_id AS department_id,
            hl.holiday_status_id AS holiday_status_id
        FROM hr_leave hl
            LEFT JOIN calendar_event ce
                ON ce.id = hl.meeting_id
            LEFT JOIN hr_employee em
                ON em.id = hl.employee_id
        WHERE 
            hl.state = 'validate');
        """)
