# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from pytz import timezone, UTC
from datetime import date, datetime, time

from odoo import _, api, fields, models
from odoo.addons.resource.models.utils import Intervals

_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = "hr.employee"

    def _get_expected_attendances(self, date_from, date_to):
        self.ensure_one()
        valid_contracts = self.sudo()._get_contracts(date_from, date_to, states=['open', 'close'])
        if not valid_contracts:
            return super()._get_expected_attendances(date_from, date_to)
        employee_tz = timezone(self.tz) if self.tz else None
        duration_data = Intervals()
        for contract in valid_contracts:
            contract_start = datetime.combine(contract.date_start, time.min, employee_tz)
            contract_end = datetime.combine(contract.date_end or date.max, time.max, employee_tz)
            calendar = contract.resource_calendar_id or contract.company_id.resource_calendar_id
            contract_intervals = calendar._work_intervals_batch(
                                    max(date_from, contract_start),
                                    min(date_to, contract_end),
                                    tz=employee_tz,
                                    resources=self.resource_id,
                                    compute_leaves=True,
                                    domain=[])[self.resource_id.id]
            duration_data = duration_data | contract_intervals
        return duration_data