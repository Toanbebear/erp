from calendar import monthrange
from datetime import date, datetime

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError


class collaboratorCancelPaymentWizard(models.TransientModel):
    _name = 'collaborator.cancel.payment.wizard'
    _description = 'Hủy phiếu thanh toán CTV'

    collaborator_id = fields.Many2one('collaborator.collaborator', string="Cộng tác viên")
    collaborator_payment = fields.Many2one('collaborator.payment', string="Phiếu chi")
    contract_id = fields.Many2one('collaborator.contract', string='Hợp đồng')
    company_id = fields.Many2one('res.company',  string='Công ty giao dịch', default=lambda self: self.env.company, )
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id')
    collaborator_payment_date = fields.Date('Ngày hủy', default=lambda self: fields.Datetime.now(), help="Ngày hủy phiếu")
    note = fields.Text('Nội dung hủy')
    collaborator_user = fields.Many2one('res.users', 'Người hủy', default=lambda self: self.env.user)
    amount = fields.Monetary('Tổng tiền hủy', tracking=True, help="Số tiền hủy trên phiếu chi")
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    company_payment = fields.Many2one('res.company', string='Công ty ghi nợ')

    def confirm(self):
        for rec in self:
            if rec.company_payment:
                amount = rec.collaborator_id.account_ids.filtered(lambda fol: fol.company_id in rec.company_payment and fol.collaborator_id in rec.collaborator_id)
                rec.collaborator_payment.write({
                    'state': 'cancelled',
                    'collaborator_payment_cancel_date': rec.collaborator_payment_date,
                    'note_cancel': rec.note,
                    'collaborator_user_cancel': rec.collaborator_user.id,
                })
                amount.write({
                    'amount_used': amount.amount_used - rec.amount
                })
            else:
                amount = rec.collaborator_id.account_ids.filtered(lambda fol: fol.company_id in rec.company_id and fol.collaborator_id in rec.collaborator_id)
                rec.collaborator_payment.write({
                    'state': 'cancelled',
                    'collaborator_payment_cancel_date': rec.collaborator_payment_date,
                    'note_cancel': rec.note,
                    'collaborator_user_cancel': rec.collaborator_user.id,
                })
                amount.write({
                    'amount_used': amount.amount_used - rec.amount
                })



