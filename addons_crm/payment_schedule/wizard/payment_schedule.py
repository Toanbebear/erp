from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PaymentSchedule(models.TransientModel):
    _name = "payment.schedule"
    _description = "Lịch trình thanh toán"

    def domain_service(self):
        booking = self._context.get('default_booking')
        service = self.env['crm.line'].sudo().search([('crm_id', '=', booking), ('stage', '!=', 'cancel')]).mapped('service_id')
        return [('id', 'in', service.ids)]

    booking = fields.Many2one('crm.lead')
    service = fields.Many2one('sh.medical.health.center.service', 'Dịch vụ', domain=domain_service)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary('Số tiền')
    total_received = fields.Monetary('Tiền đã thanh toán')
    number = fields.Integer('Số lần thu tiền còn lại')

    @api.onchange('service', 'booking')
    def onchange_service(self):
        if self.service and self.booking:
            line = self.env['crm.line'].sudo().search([('crm_id', '=', self.booking.id), ('stage', '!=', 'cancel'), ('service_id', '=', self.service.id)])
            self.amount = sum(line.mapped('total'))
            self.total_received = line.total_received

    def confirm(self):
        schedule_exist = self.env['statement.service'].sudo().search([('booking_id', '=', self.booking.id), ('service_id', '=', self.service.id)])
        schedule_exist.unlink()
        total_received = sum(self.env['crm.line'].sudo().search([('crm_id', '=', self.booking.id), ('service_id', '=', self.service.id)]).mapped('total_received'))

        if total_received > 0:
            sale_payment = self.env['crm.sale.payment'].sudo().search([('booking_id', '=', self.booking.id), ('service_id', '=', self.service.id), ('account_payment_id', '!=', False), ('payment_type', '=', 'inbound')], order='payment_date desc')
            self.env['statement.service'].sudo().create({
                'scheduled_date': sale_payment[0].payment_date if sale_payment else False,
                'booking_id': self.booking.id,
                'partner_id': self.booking.partner_id.id,
                'company_id': self.env.company.id,
                'amount': total_received,
                'service_id': self.service.id,
                'paid': True
            })
        amount_due = self.amount - total_received
        if amount_due <= 0:
            raise ValidationError('Dịch vụ này đã thanh toán đủ')
        else:
            datas = []
            for i in range(1, self.number + 1):
                datas.append({
                    'booking_id': self.booking.id,
                    'partner_id': self.booking.partner_id.id,
                    'company_id': self.env.company.id,
                    'amount': amount_due/self.number,
                    # 'note': 'Thanh toán lần thứ %s' %i,
                    'service_id': self.service.id
                })
            self.env['statement.service'].sudo().create(datas)
