import logging
import pytz
from markupsafe import Markup
from datetime import date, datetime, time, timedelta

from odoo import api, models, fields

_logger = logging.getLogger(__name__)

def _get_local_time(date, tz):
    return pytz.utc.localize(date).astimezone(tz)

class ReportHrEmployee(models.AbstractModel):
    _inherit = "report.hr_employee_attendance_report.hr_employee"

    @api.model
    def _get_report_values(self, docids, data=None):
        res = super()._get_report_values(docids, data)

        time_stamps = self._get_timestamp_data(res)

        # Merge timestamp data into attendance records
        attendances = res.get("attendances", {})
        for employee_id, attendance_list in attendances.items():
            employee_time_stamps = time_stamps.get(employee_id, [])
            for i, attendance in enumerate(attendance_list):
                if i < len(employee_time_stamps):
                    attendance["ts"] = employee_time_stamps[i].get("ts", "")
                else:
                    attendance["ts"] = ""

        return res

    def _get_timestamp_data(self, res):
        time_stamps_dict = {}
        user_tz = pytz.timezone(self.env.context.get("tz") or "UTC")
        time_stamps = {}
        all_attendances = res.get("attendances")
        dates = res.get("dates")
        if all_attendances and dates:
            for key, value in all_attendances.items():
                employee_id = key
                time_stamps_dict[employee_id] = []
                for att in value:
                    date = att.get("date")
                    dt = fields.Datetime.to_datetime(date)
                    attendance_ids = self.env["hr.attendance"].search(
                        [
                            ("employee_id", "=", employee_id),
                            # "&",
                            # ("check_in", "<=", end_date),
                            # ("check_out", ">=", start_date),
                        ]
                    )
                    attendance_ids = attendance_ids.filtered(
                        lambda a: a.check_in.date() == dt.date() and a.check_out - a.check_in > timedelta(seconds=3)
                    )

                    time_stamps = []

                    for attendance in attendance_ids:
                        time_stamps.append(
                            {
                                "check_in": attendance.check_in,
                                "check_out": attendance.check_out,
                            }
                        )
                    sorted_time_stamps = sorted(time_stamps, key=lambda x: x["check_in"])
                    time_stamps_string = Markup(
                        " ".join(
                            [
                                f"{_get_local_time(ts['check_in'], user_tz).strftime('%H:%M')}-{_get_local_time(ts['check_out'], user_tz).strftime('%H:%M')}<br>"
                                for ts in sorted_time_stamps
                            ]
                        )
                    )
                    ts_data_dict = {
                        "date": date,
                        "ts": time_stamps_string
                    }
                    time_stamps_dict[employee_id].append(ts_data_dict)

        return time_stamps_dict


