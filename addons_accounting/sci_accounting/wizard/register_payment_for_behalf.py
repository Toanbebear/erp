from odoo import fields, models, api
from collections import defaultdict


class RegisterPaymentBehalf(models.TransientModel):
    _name = 'register.payment.behalf.wizard'
    _description = 'Description'

    company_id = fields.Many2one(comodel_name='res.company', string='Gửi tới chi nhánh')
    register_payment = fields.Many2one(comodel_name='account.register.payment.behalf', readonly=True)
    label = fields.Selection(selection=[('1', 'Bình thường'), ('2', 'Ưu tiên'), ('3', 'Khẩn cấp')], string='Phân loại mức ưu tiên')

    def request_payment_behalf(self):
        # Tạo mới bản ghi đề nghị duyệt chi
        file = self.register_payment
        behalf_line = file.behalf_lines
        line = []
        for element in behalf_line:
            line.append((0, 0, {
                'partner_id': element.partner_id.id,
                'invoice': element.invoice.id,
                'invoice_date': element.invoice_date,
                'communication': element.communication,
                'amount_register': element.amount_register,
                'currency_id': element.currency_id.id,
                'state': 'wait'}))

        RegisterPaymentBehalf = self.env['account.register.payment.behalf']

        val = {'date_register': file.date_register,
               'company_id': self.company_id.id,
               'communication': file.communication,
               'behalf_lines': line,
               'type': 'dc',
               'original_record': file.id,
               'is_debt': self.register_payment.is_debt,
               'label': self.label,
               }
        RegisterPaymentBehalf.sudo().create(val)
        file.sudo().write({
            'state': 'sent'
        })
        for element in file.sudo().behalf_lines:
            element.write({'state': 'sent'})
