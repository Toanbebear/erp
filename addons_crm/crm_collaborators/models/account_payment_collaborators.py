import json
import logging
from datetime import date, timedelta

from lxml import etree

from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError
from num2words import num2words

_logger = logging.getLogger(__name__)


class AccountPaymentCTV(models.Model):
    _name = 'account.payment.ctv'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Phiếu chi cho cộng tác viên'

    name = fields.Char(string='Tên')
    ctv_payment_type = fields.Selection(
        [('outbound', 'Chi Tiền cộng tác viên')], string="Loại thanh toán", default='outbound')
    ctv_payment_method = fields.Selection(
        [('tm', 'Tiền mặt'), ('ck', 'Chuyển khoản')], string='Hình thức thanh toán', default='tm')
    ctv_partner_type = fields.Selection(
        [('customer', 'Khách hàng')], string='Loại đối tác', default='customer')
    collaborators_id = fields.Many2one('crm.collaborators', 'Cộng tác viên',)
    contract_id = fields.Many2one('collaborators.contract', string='Hợp đồng')
    phone = fields.Char('Điện thoại')
    pass_port = fields.Char('CMTND/CCCD ')
    email = fields.Char('Email')
    collaborators_amount = fields.Monetary('Tổng tiền hiện có')
    partner_id = fields.Many2one('res.partner', string='Đối tác')
    payment_method_id = fields.Many2one('account.payment.method', 'Phương thức thanh toán', default=lambda self: self.env.ref('account.account_payment_method_manual_in').id)
    company_id = fields.Many2one('res.company', related='ctv_journal_id.company_id', string='Công ty', default=lambda self: self.env.company,)
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id', store=True)
    amount = fields.Monetary('Tổng tiền', tracking=True,  help="Số tiền chi trả cho cộng tác viên")
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    ctv_amount_vnd = fields.Float('Tổng tiền bằng số', compute='set_amount_vnd', digits=(3, 0))
    ctv_text_total = fields.Text('Tổng tiền bằng chữ')
    ctv_payment_date = fields.Date('Ngày', default=lambda self: fields.Datetime.now(), help="Ngày chi trả tiền cho cộng tác viên")
    ctv_communication = fields.Text('Nội dung giao dịch')
    ctv_user = fields.Many2one('res.users', 'Người chi', default=lambda self: self.env.user)
    ctv_journal_id = fields.Many2one('account.journal', 'Sổ nhật ký')
    state = fields.Selection([('draft', 'Nháp'), ('posted', 'Đã xác nhận'), ('cancelled', 'Đã hủy')], default='draft', string="Trạng thái")
    check_ctv = fields.Boolean('Check cộng tác viên', default=True)
    payment_id = fields.One2many('account.payment', 'payment_ctv', 'Phiếu chi và Bút toán liên quan')

    @api.constrains('amount')
    def check_amount(self):
        for rec in self:
            if rec.collaborators_amount < rec.amount:
                raise ValidationError('Số tiền bạn nhập đã vượt quá số tiền hiện có của cộng tác viên!')
    #         if int(self.amount) != total:
    #             raise ValidationError('Tiền nhận được cần được chia đủ vào các khóa học')

    @api.onchange('amount')
    def onchange_amount(self):
        if self.amount and self.amount > 0:
            # neu currency là VND
            if self.currency_id == self.env.ref('base.VND'):
                self.ctv_text_total = num2words(round(self.amount), lang='vi_VN') + " đồng"
            # neu currency khác
            else:
                self.ctv_text_total = num2words(round(self.ctv_amount_vnd)) + " đồng"
        elif self.amount and self.amount < 0:
            raise ValidationError(
                _('Số tiền thanh toán không hợp lệ!'))
        else:
            self.ctv_text_total = "Không đồng"

    @api.onchange('currency_id')
    def back_value(self):
        # quy đổi tiền về tiền việt
        self.ctv_text_total = num2words(round(self.ctv_amount_vnd), lang='vi_VN') + " đồng"

    @api.depends('amount')
    def set_amount_vnd(self):
        for rec in self:
            rec.ctv_amount_vnd = 0
            if rec.amount:
                if rec.currency_id and rec.currency_id :
                    rec.ctv_amount_vnd = rec.amount * 1
                # quy đổi tiền về tiền việt
                rec.ctv_text_total = num2words(round(rec.ctv_amount_vnd), lang='vi_VN') + " đồng"

    @api.onchange('company_id', 'collaborators_id')
    def onchange_company_id(self):
        for rec in self:
            if rec.collaborators_id:
                        rec.partner_id = rec.collaborators_id.partner_id
                        rec.contract_id = rec.collaborators_id.contract_ids.filtered(lambda fol: fol.stage in (
                        'new', 'open') and fol.collaborators_id in rec.collaborators_id and fol.company_id in rec.company_id)
                        # rec.collaborators_amount = rec.payment_ctv.filtered(lambda fol: fol.company_id in rec.company_id and fol.collaborators_id in rec.collaborators_id)
                        amount = rec.collaborators_id.payment_ctv.filtered(
                            lambda fol: fol.company_id in rec.company_id and fol.collaborators_id in rec.collaborators_id)
                        rec.collaborators_amount = amount.amount_remain
                        rec.phone = rec.collaborators_id.phone
            if rec.collaborators_id and rec.company_id:
                        rec.partner_id = rec.collaborators_id.partner_id
                        rec.contract_id = rec.collaborators_id.contract_ids.filtered(lambda fol: fol.stage in (
                        'new', 'open') and fol.collaborators_id in rec.collaborators_id and fol.company_id in rec.company_id)
                        # rec.collaborators_amount = rec.payment_ctv.filtered(lambda fol: fol.company_id in rec.company_id and fol.collaborators_id in rec.collaborators_id)
                        amount = rec.collaborators_id.payment_ctv.filtered(
                            lambda fol: fol.company_id in rec.company_id and fol.collaborators_id in rec.collaborators_id)
                        rec.collaborators_amount = amount.amount_remain
                        rec.phone = rec.collaborators_id.phone

    def cancel(self):
        self.write({'state': 'cancelled'})

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_('Bạn chỉ có thể xoá khi ở trạng thái nháp, nếu có thể bạn hãy lưu trữ!'))
        return super(AccountPaymentCTV, self).unlink()

    def post(self):
        for rec in self:
            if not rec.name:
                if rec.ctv_payment_type == 'outbound':
                    sequence_code = 'account.payment.customer.pay.ctv'
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.ctv_payment_date)
            if rec.amount:
                total_ctv = rec.collaborators_amount - rec.amount
                amount = rec.collaborators_id.payment_ctv.filtered(
                    lambda fol: fol.company_id in rec.company_id and fol.collaborators_id in rec.collaborators_id)
                amount.amount_remain = total_ctv
                amount.amount_used = amount.amount_used + rec.amount
            rec.write({'state': 'posted'})

            payment = rec.env['account.payment'].sudo().create({
                'check_ctv': True,
                'payment_type': 'outpay',
                'payment_method': 'tm' if rec.ctv_payment_method == 'tm' else 'ck',
                'partner_type': 'customer',
                'collaborators_id': rec.collaborators_id.id,
                'contract_id': rec.contract_id.id,
                'partner_id': rec.partner_id.id,
                'collaborators_amount': rec.collaborators_amount,
                'amount': rec.amount,
                'payment_date': rec.ctv_payment_date,
                'communication': rec.ctv_communication,
                'user': rec.ctv_user.id,
                'journal_id': rec.ctv_journal_id.id,
                'payment_method_id': rec.payment_method_id.id,
                'payment_ctv': rec.id,
            })
            payment.post()








