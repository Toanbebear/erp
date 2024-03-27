from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    _description = 'Phiếu thanh toán'

    payment_list_id = fields.Many2one('payment.list', string='Bảng kê thanh toán', readonly=True)
    payment_list_state = fields.Char(string='Trạng thái bảng kê')

    def post(self):
        res = super(AccountPayment, self).post()
        payment_list = self.payment_list_id
        if payment_list:
            payments = self.env['account.payment'].search([('payment_list_id', '=', self.payment_list_id.id)])

            # Check thông tin account.payment khớp với payment.list
            if payment_list.payment_type != self.payment_type:
                raise ValidationError(_("Loại thanh toán khác với bảng kê."))
            elif payment_list.partner_type != self.partner_type:
                raise ValidationError(_("Loại đối tác khác với bảng kê."))
            elif payment_list.partner_id.id != self.partner_id.id:
                raise ValidationError(_("Đối tác khác với bảng kê."))
            elif payment_list.company_id.id != self.company_id.id:
                raise ValidationError(_("Công ty với bảng kê."))

            if payments:
                if all(pay.state != 'draft' for pay in payments):
                    self.payment_list_id.write({
                        'state': 'done'
                    })
        return res

    def cancel(self):
        res = super(AccountPayment, self).cancel()
        payment_list = self.payment_list_id
        if payment_list:
            payments = self.env['account.payment'].search([('payment_list_id', '=', self.payment_list_id.id)])

            # Check thông tin account.payment khớp với payment.list
            if payment_list.payment_type != self.payment_type:
                raise ValidationError(_("Loại thanh toán khác với bảng kê."))
            elif payment_list.partner_type != self.partner_type:
                raise ValidationError(_("Loại đối tác khác với bảng kê."))
            elif payment_list.partner_id.id != self.partner_id.id:
                raise ValidationError(_("Đối tác khác với bảng kê."))
            elif payment_list.company_id.id != self.company_id.id:
                raise ValidationError(_("Công ty với bảng kê."))

            if payments:
                if all(pay.state != 'draft' for pay in payments):
                    self.payment_list_id.write({
                        'state': 'done'
                    })
        return res

    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        payment_list = self.payment_list_id
        if payment_list:
            self.write({'payment_list_state': 'draft'})
        if payment_list.state != 'waiting':
            payment_list.write({'state': 'waiting'})
        return res
