import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ReportHrEmployee(models.AbstractModel):
    _inherit = "report.hr_employee_attendance_report.hr_employee"

    @api.model
    def _get_report_values(self, docids, data=None):
        return super(ReportHrEmployee, self.with_context(show_paid_out_overtime=True))._get_report_values(docids, data)
