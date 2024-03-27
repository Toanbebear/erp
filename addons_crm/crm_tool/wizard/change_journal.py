from odoo import models, fields
from odoo.exceptions import ValidationError


class ChangeJournal(models.TransientModel):
    _name = "change.journal"
    _description = "Đổi sổ nhật ký cho phiếu thu/chi hoặc Bút toán"

    def domain_journal(self):
        journal = self.env['account.journal'].sudo().search([('company_id', '=', self.env.company.id)])
        return [('id', 'in', journal.ids)]

    type = fields.Selection([('payment', 'Phiếu thu'), ('move', 'Bút toán phát sinh')], string='Bạn muốn đổi ...')
    journal_id = fields.Many2one('account.journal', string='Sổ nhật ký', domain=domain_journal)
    move_id = fields.Many2one('account.move', string='Bút toán')
    payment_id = fields.Many2one('account.payment')

    def confirm(self):
        if self.type == 'payment':
            if not self.payment_id:
                raise ValidationError('Lỗi không tìm thấy phiếu thu/chi. Liên hệ Admin.')
            payment = self.payment_id
            if payment.company_id.id != self.env.company.id:
                raise ValidationError('Vui lòng chuyển sang chi nhánh %s để thao tác tiếp.' % payment.company_id.name)
            payment.journal_id = self.journal_id.id
            move = payment.move_id
            move_lines = self.env['account.move.line'].sudo().search([('move_id', '=', move.id)])
            if move_lines:
                for line in move_lines:
                    line.journal_id = self.journal_id.id
                    if line.account_id.id == move.journal_id.default_debit_account_id.id:
                        line.account_id = self.journal_id.default_debit_account_id.id
            self.env.cr.execute(""" UPDATE account_move
                                    SET journal_id = %s
                                    WHERE id = %s;""" % (self.journal_id.id, move.id))
        elif self.type == 'move':
            if not self.move_id:
                raise ValidationError('Không tìm thấy bút toán cần cập nhật. Vui lòng liên hệ Admin')
            if self.move_id.company_id != self.journal_id.company_id:
                raise ValidationError('Kiểm tra lại công ty của sổ nhật ký với công ty của bút toán')
            self.env.cr.execute(""" UPDATE account_move
                                    SET journal_id = %s
                                    WHERE id = %s;""" % (self.journal_id.id, self.move_id.id))
