from odoo import api, fields, models, _

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    from_time = fields.Float(default=0.0)
    until_time = fields.Float(default=0.0)
    unit_amount = fields.Float(compute='_compute_unit_amount', readonly=False, store=True)

    @api.depends('from_time', 'until_time')
    def _compute_unit_amount(self):
        for rec in self:
            if rec.from_time < rec.until_time:
                rec.unit_amount =  rec.until_time - rec.from_time