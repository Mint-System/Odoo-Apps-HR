import logging
import pytz

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _cron_absence_detection(self):
        """
        OVERWRITE: The absence detection runs for employee of attendance user group only.
        """
        yesterday = datetime.today().replace(hour=0, minute=0, second=0) - relativedelta(days=1)
        companies = self.env['res.company'].search([('absence_management', '=', True)])
        if not companies:
            return

        checked_in_employees = self.env['hr.attendance.overtime'].search([('date', '=', yesterday),
                                                                          ('adjustment', '=', False)]).employee_id

        technical_attendances_vals = []
        absent_employees = self.env['hr.employee'].search([('id', 'not in', checked_in_employees.ids),
                                                           ('company_id', 'in', companies.ids)])

        absent_employees = absent_employees.filtered(lambda e: e.user_id and e.user_id.has_group("hr_attendance_user_acl.group_hr_attendance_user"))

        for emp in absent_employees:
            local_day_start = pytz.utc.localize(yesterday).astimezone(pytz.timezone(emp._get_tz()))
            technical_attendances_vals.append({
                'check_in': local_day_start.strftime('%Y-%m-%d %H:%M:%S'),
                'check_out': (local_day_start + relativedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'in_mode': 'technical',
                'out_mode': 'technical',
                'employee_id': emp.id
            })

        technical_attendances = self.env['hr.attendance'].create(technical_attendances_vals)
        to_unlink = technical_attendances.filtered(lambda a: a.overtime_hours == 0)

        body = _('This attendance was automatically created to cover an unjustified absence on that day.')
        for technical_attendance in technical_attendances - to_unlink:
            technical_attendance.message_post(body=body)

        # to_unlink.unlink()