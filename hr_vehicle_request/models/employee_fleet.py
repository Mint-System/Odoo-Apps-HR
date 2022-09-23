from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class FleetReservedTime(models.Model):
    _name = 'fleet.reserved'
    _description = 'Reserved Time'

    employee = fields.Many2one('hr.employee')
    date_from = fields.Datetime(string='Reserved Date From')
    date_to = fields.Datetime(string='Reserved Date To')
    reserved_obj = fields.Many2one('fleet.vehicle')

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, rec.reserved_obj.display_name))
        return res


class FleetVehicleInherit(models.Model):
    _inherit = 'fleet.vehicle'

    check_availability = fields.Boolean(default=True, copy=False)
    reserved_time = fields.One2many('fleet.reserved', 'reserved_obj', readonly=1, ondelete='cascade')


class EmployeeFleet(models.Model):
    _name = 'employee.fleet'
    _description = 'Employee Vehicle Request'
    _inherit = 'mail.thread'

    @api.constrains('date_from', 'date_to')
    def onchange_date_to(self):
        for reservation in self:
            if reservation.date_from > reservation.date_to:
                raise Warning(_('Date To must be greater than Date From.'))

    # @api.onchange('date_from', 'date_to')
    # def check_availability(self):
    #     if self.date_from and self.date_to:
    #         vehicle_ids = self.env['fleet.vehicle'].search([])
    #         for reservation in vehicle_ids.reserved_time:
    #             if reservation.date_from and reservation.date_to:
    #                 if reservation.date_from <= self.date_from <= reservation.date_to:
    #                     vehicle_ids.write({'check_availability': False})
    #                 elif self.date_from < reservation.date_from:
    #                     if reservation.date_from <= self.date_to <= reservation.date_to:
    #                         vehicle_ids.write({'check_availability': False})
    #                     elif self.date_to > reservation.date_to:
    #                         vehicle_ids.write({'check_availability': False})
    #                     else:
    #                         vehicle_ids.write({'check_availability': True})
    #                 else:
    #                     vehicle_ids.write({'check_availability': True})

    reserved_fleet_id = fields.Many2one('fleet.reserved', invisible=1, copy=False)
    name = fields.Char(string='Request Number', copy=False)
    employee = fields.Many2one('hr.employee', required=1, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.employee_id)
    req_date = fields.Date(string='Requested Date', default=fields.Date.context_today, required=1, readonly=True, states={'draft': [('readonly', False)]}, help='Requested Date')
    fleet = fields.Many2one('fleet.vehicle', string='Vehicle', required=1, readonly=True, states={'draft': [('readonly', False)]})
    date_from = fields.Datetime(string='From', required=1, readonly=True, states={'draft': [('readonly', False)]})
    date_to = fields.Datetime(string='To', required=1, readonly=True, states={'draft': [('readonly', False)]})
    returned_date = fields.Datetime(readonly=1)
    purpose = fields.Text(string='Purpose', required=1, readonly=True, states={'draft': [('readonly', False)]}, help='Purpose')
    state = fields.Selection([('draft', 'Draft'), ('waiting', 'Waiting for Approval'), ('cancel', 'Cancel'), ('confirm', 'Approved'), ('reject', 'Rejected'), ('return', 'Returned')], string='State', default='draft')

    def unlink(self):
        if self.reserved_fleet_id:
            self.reserved_fleet_id.unlink()
        return super().unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('employee.fleet')
        return super(EmployeeFleet, self).create(vals)

    def send(self):    
        check_availability = False
        for reservation in self.fleet.reserved_time:
            if reservation.date_from and reservation.date_to:
                if reservation.date_from <= self.date_from <= reservation.date_to:
                    check_availability = True
                elif self.date_from < reservation.date_from:
                    if reservation.date_from <= self.date_to <= reservation.date_to:
                        check_availability = True
                    elif self.date_to > reservation.date_to:
                        check_availability = True
                    else:
                        check_availability = False
                else:
                    check_availability = False
        if not check_availability:
            reserved_id = self.fleet.reserved_time.create({
                'employee': self.employee.id,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'reserved_obj': self.fleet.id,
            })
            self.write({'reserved_fleet_id': reserved_id.id})
            self.state = 'waiting'
        else:
            raise Warning(_('Sorry this vehicle is already requested by another employee.'))

    def approve(self):
        self.fleet.fleet_status = True
        self.state = 'confirm'
        mail_content = _('Hi %s,<br>Your vehicle request for the reference %s is approved.') % (self.employee.name, self.name)
        main_content = {
            'subject': _('%s: Approved') % self.name,
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.employee.work_email,
        }
        mail_id = self.env['mail.mail'].create(main_content)
        mail_id.mail_message_id.body = mail_content
        mail_id.send()
        if self.employee.user_id:
            mail_id.mail_message_id.write({'partner_ids': [(4, self.employee.user_id.partner_id.id)]})

    def reject(self):
        self.reserved_fleet_id.unlink()
        self.state = 'reject'
        mail_content = _('Hi %s,<br>Sorry, Your vehicle request for the reference %s is Rejected.') % (self.employee.name, self.name)
        main_content = {
            'subject': _('%s: Approved') % self.name,
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.employee.work_email,
        }
        mail_id = self.env['mail.mail'].create(main_content)
        mail_id.mail_message_id.body = mail_content
        mail_id.send()
        if self.employee.user_id:
            mail_id.mail_message_id.write({'partner_ids': [(4, self.employee.user_id.partner_id.id)]})

    def cancel(self):
        if self.reserved_fleet_id:
            self.reserved_fleet_id.unlink()
        self.state = 'cancel'

    def draft(self):
        self.state = 'draft'

    def returned(self):
        self.reserved_fleet_id.sudo().unlink()
        self.returned_date = fields.datetime.now()
        self.state = 'return'