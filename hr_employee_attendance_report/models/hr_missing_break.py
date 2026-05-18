import logging

from odoo import fields, models, _

_logger = logging.getLogger(__name__)


BREAK_DURATION_HOURS = 0.5


class HrMissingBreak(models.Model):
    _name = "hr.missing.break"
    _description = "Missing Break"

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, ondelete='cascade', index=True)
    working_day = fields.Datetime(string="Date", default=fields.Datetime.now, required=True)

    deducted = fields.Boolean(
        string="Break Deducted",
        default=False,
        readonly=True,
        help="When checked, the break penalty has already been applied to overtime. "
             "Running the action again will have no effect."
    )
    deducted_on = fields.Datetime(
        string="Deducted On",
        readonly=True
    )


    def action_deduct_missing_break(self):
        """
        Deduct the missing break (30 min) from the employee's overtime for the
        working day. Safe to run multiple times — already-deducted records are
        skipped. Designed to be called from a server action on hr.employee or
        directly on hr.missing.break records.
        """
        # Support being called from hr.employee server action:
        # active_model == 'hr.employee' → find all pending breaks for selection
        if self.env.context.get('active_model') == 'hr.employee':
            employee_ids = self.env.context.get('active_ids', [])
            records = self.search([
                ('employee_id', 'in', employee_ids),
                ('deducted', '=', False),
            ])
        else:
            records = self.filtered(lambda r: not r.deducted)

        if not records:
            raise UserError(_("No pending missing breaks to deduct. "
                              "All selected breaks have already been processed."))

        OvertimeModel = self.env['hr.attendance.overtime']
        AttendanceModel = self.env['hr.attendance']

        deducted_count = 0
        for break_rec in records:
            employee = break_rec.employee_id
            # Normalise to a date for comparison (working_day is Datetime)
            day_date = fields.Date.context_today(
                self, timestamp=break_rec.working_day
            )

            # Find the overtime record for this employee / day
            # hr.attendance.overtime stores one record per employee per day.
            overtime = OvertimeModel.search([
                ('employee_id', '=', employee.id),
                ('date', '=', day_date),
            ], limit=1)

            if overtime:
                # Adjust existing overtime (can go negative — intentional)
                new_duration = overtime.duration - BREAK_DURATION_HOURS
                overtime.write({'duration': new_duration})
                _logger.info(
                    "Missing break deducted: employee=%s day=%s "
                    "overtime %.2f → %.2f h",
                    employee.name, day_date,
                    overtime.duration + BREAK_DURATION_HOURS, new_duration
                )
            else:
                # No overtime record yet → create one with negative duration
                # so the deduction is still recorded even when OT is 0.
                OvertimeModel.create({
                    'employee_id': employee.id,
                    'date': day_date,
                    'duration': -BREAK_DURATION_HOURS,
                    'adjustment': True,   # marks it as a manual adjustment
                })
                _logger.info(
                    "Missing break deducted (no prior OT): employee=%s day=%s "
                    "→ -%.2f h overtime created",
                    employee.name, day_date, BREAK_DURATION_HOURS
                )


            # Mark as deducted — idempotency guard
            break_rec.write({
                'deducted': True,
                'deducted_on': fields.Datetime.now(),
            })
            deducted_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Missing Breaks Deducted",
                'message': _(
                    "%d missing break(s) of 30 min have been deducted from overtime."
                ) % deducted_count,
                'type': 'success',
                'sticky': False,
            },
        }

