import logging

from odoo import api, models

from . import attendance_data

_logger = logging.getLogger(__name__)


class ReportHrEmployeeEnhanced(models.AbstractModel):
    _name = "report.hr_employee_attendance_report.hr_employee_enhanced"
    _description = "Attendance and leave report Enhanced"

    @api.model
    def _get_report_values(self, docids, data=None):
        return attendance_data._get_report_values(self, docids, data, self._name)
