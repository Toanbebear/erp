import datetime

from odoo import models, fields, api
from datetime import timedelta, MAXYEAR
from odoo.exceptions import ValidationError


class CreateAnAppointment(models.TransientModel):
    _name = "create.an.appointment"
    _description = 'Create An Appointment'

    opportunity_id = fields.Many2one('crm.lead', string='Bookings',
                                     domain="[('partner_id', '=', customer_id), ('type', '=', 'opportunity')]")
    customer_id = fields.Many2one('res.partner', string='Khách hàng')
    domain_physician = fields.Many2many('sh.medical.physician', compute="_get_physician_by_booking_date")
    physician = fields.Many2one('sh.medical.physician', string='Bác sĩ/Trợ thủ',
                                domain="[('id','not in',domain_physician)]")
    services = fields.Many2many('sh.medical.health.center.service', string='Danh sách dịch vụ')
    start_datetime = fields.Datetime('Ngày/giờ bắt đầu', default=datetime.datetime.now())
    duration = fields.Float('Khoảng thời gian', default=1)
    name = fields.Text('Nội dung')
    company_id = fields.Many2one('res.company', string='Chi nhánh', domain="[('id', 'in', allowed_company_ids)]",
                                 default=lambda self: self.env.company)
    users = fields.Many2many('res.users', string='Danh sách được nhắc lịch', default=lambda self: self.env.user)

    @api.depends('start_datetime')
    def _get_physician_by_booking_date(self):
        for record in self:
            record.domain_physician = False
            if record.start_datetime:
                end_date = record.start_datetime + timedelta(hours=1)
                physicians = record.env['doctor.schedule'].search(
                    [('start_datetime', '<=', record.start_datetime),
                     ('end_datetime', '>=', end_date)]).mapped('physician')
                record.domain_physician = [(6, 0, physicians.ids)]

    @api.onchange('start_datetime')
    def clear_physician(self):
        self.physician = False

    # @api.onchange('customer_id', 'physician', 'services')
    # def auto_name(self):
    #     self.name = False
    #     description = '[%s]%s\n%s' % (self.opportunity_id.name, self.customer_id.name, self.name)
    #     self.name = description

    @api.onchange('opportunity_id')
    def get_services(self):
        if self.opportunity_id:
            self.services = False
            lines = self.opportunity_id.mapped('crm_line_ids')
            services = lines.mapped('service_id')
            return {'domain': {'services': [('id', 'in', services.ids)]}}

    def request_appointment(self):
        stop = self.start_datetime + timedelta(hours=self.duration) + timedelta(seconds=1)
        partner_ids = [self.customer_id.id, self.env.user.partner_id.id]
        if self.users:
            partner_ids += self.users.mapped('partner_id').ids
        name = '[%s]%s - %s' % (self.opportunity_id.name, self.customer_id.name, self.name)
        self.env['calendar.event'].sudo().create({
            'name': name,
            'customer_id': self.customer_id.id,
            'user_id': self.env.user.id,
            'start': self.start_datetime,
            'stop': stop,
            'duration': self.duration,
            'physician': self.physician.id,
            'alarm_ids': [(6, 0, [self.env.ref('calendar.alarm_notif_1').id])],
            'services': [(6, 0, self.services.ids)] if self.services else False,
            'opportunity_id': self.opportunity_id.id if self.opportunity_id else False,
            'company_id': self.company_id.id,
            'location': self.company_id.name,
            'state': 'confirm',
        })
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = 'Tạo lịch hẹn thành công!! \nHệ thống sẽ nhắc lịch trước 15 phút.'
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view_id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.location = False
        self.users = [(4, self.env.user.id)]
        if self.company_id:
            self.location = self.company_id.name

