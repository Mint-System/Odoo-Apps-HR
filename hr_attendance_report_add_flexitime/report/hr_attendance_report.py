from odoo import api, fields, models
from odoo import tools

class HRAttendanceReport(models.Model):
    _inherit = "hr.attendance.report"


    planned_hours = fields.Float("Planned Hours", readonly=True)
    diff_hours = fields.Float("+/-", readonly=True)


    @api.model
    def _select(self):
        return super()._select() + """,
            COALESCE(ph.planned_hours, 0) AS planned_hours,
            (hra.worked_hours - COALESCE(ph.planned_hours, 0)) AS diff_hours
        """

    def _join(self):
        return super()._join() + """
            LEFT JOIN hr_employee_planned_hours ph
                ON ph.employee_id = hra.employee_id
                AND ph.date = hra.check_in
        """

    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, self._table)
    #     self.env.cr.execute(f"""
    #         CREATE OR REPLACE VIEW {self._table} AS (
    #             {self._select()}
    #             {self._from()}
    #             {self._join()}
    #         )
    #     """)


    def init(self):
        cr = self.env.cr
        tools.drop_view_if_exists(cr, self._table)

        # --- SAFETY CHECK: skip creation if planned-hours table missing ---
        cr.execute("""
            SELECT COUNT(*) FROM pg_class
            WHERE relname = 'hr_employee_planned_hours'
        """)
        if cr.fetchone()[0] == 0:
            # Planned hours table not created yet -> skip
            return

        # --- Create the view ---
        cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                {self._select()}
                {self._from()}
                {self._join()}
            )
        """)

