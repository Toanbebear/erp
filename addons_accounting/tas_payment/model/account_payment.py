# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountPayment(models.Model):
    _inherit = "account.payment"

    move_id = fields.Many2one("account.move", string="Bút toán thanh toán")

    def post(self):
        res = super(AccountPayment, self).post()

        for record in self:
            if record.journal_id.type in "cash":
                if record.payment_type == "inbound":
                    for move_line_id in record.move_line_ids:
                        record.move_id = move_line_id.move_id
                        move_line_id.move_id.tas_type = "inbound"
                        move_line_id.move_id.nguoi_nhan = self.partner_id
                        move_line_id.move_id.address = self.partner_id.contact_address
                        move_line_id.move_id.action_create_ma_phieu()
                        return res
                if record.payment_type == "outbound":
                    print(record.move_line_ids)
                    for move_line_id in record.move_line_ids:
                        record.move_id = move_line_id.move_id
                        move_line_id.move_id.tas_type = "outbound"
                        move_line_id.move_id.nguoi_nhan = self.partner_id
                        move_line_id.move_id.address = self.partner_id.contact_address
                        move_line_id.move_id.action_create_ma_phieu()
                        return res

            else:
                if record.journal_id.type == "bank":
                    if record.payment_type == "inbound":
                        for move_line_id in record.move_line_ids:
                            record.move_id = move_line_id.move_id
                            move_line_id.move_id.tas_type = "credit"
                            move_line_id.move_id.nguoi_nhan = self.partner_id
                            move_line_id.move_id.address = self.partner_id.contact_address
                            move_line_id.move_id.action_create_ma_phieu()
                            return res
                    if record.payment_type == "outbound":
                        for move_line_id in record.move_line_ids:
                            record.move_id = move_line_id.move_id
                            move_line_id.move_id.tas_type = "debit"
                            move_line_id.move_id.nguoi_nhan = self.partner_id
                            move_line_id.move_id.address = self.partner_id.contact_address
                            move_line_id.move_id.action_create_ma_phieu()
                            return res

        return res

    def _prepare_payment_moves(self):
        all_move_vals = super(AccountPayment, self)._prepare_payment_moves()

        for move in all_move_vals:
            line = move.get('line_ids')[0][2]
            payment_id = int(line.get('payment_id'))
            move['ref'] += ' - ' + self.env['account.payment'].browse(payment_id).name

        return all_move_vals


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.payment.register"

    payment_method = fields.Selection(
        [('tm', 'Tiền mặt'), ('ck', 'Chuyển khoản'), ('nb', 'Thanh toán nội bộ'), ('pos', 'Quẹt thẻ qua POS'),
         ('vdt', 'Thanh toán qua ví điện tử')], string='Hình thức thanh toán')

    def _prepare_payment_vals(self, invoices):
        res = super(AccountRegisterPayments, self)._prepare_payment_vals(invoices)

        if self.payment_method:
            res.update({
                'payment_method': self.payment_method,
            })
        return res