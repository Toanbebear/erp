import logging

from num2words import num2words

from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
PAYMENT_TYPE = [
    ('tai_don_vi', 'Tại đơn vị'),
    ('chi_ho', 'Chi hộ'),
]

class CollaboratorPayment(models.Model):
    _name = 'collaborator.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Phiếu chi'

    name = fields.Char(string='Mã phiếu', default='New')
    collaborator_payment_type = fields.Selection(
        [('outbound', 'Chi Tiền cộng tác viên')], string="Loại thanh toán", default='outbound')
    collaborator_payment_method = fields.Selection(
        [('tm', 'Tiền mặt'), ('ck', 'Chuyển khoản')], string='Hình thức thanh toán', default='tm')
    collaborator_partner_type = fields.Selection(
        [('customer', 'Khách hàng')], string='Loại đối tác', default='customer')

    collaborator_id = fields.Many2one('collaborator.collaborator', 'Cộng tác viên')
    contract_id = fields.Many2one('collaborator.contract', string='Hợp đồng')

    phone = fields.Char('Điện thoại')
    passport = fields.Char('CMTND/CCCD ')
    email = fields.Char('Email')

    collaborator_amount = fields.Monetary('Tổng tiền hiện có')

    # partner_id = fields.Many2one('res.partner', string='Đối tác')

    payment_method_id = fields.Many2one('account.payment.method', 'Phương thức thanh toán',
                                        default=lambda self: self.env.ref(
                                            'account.account_payment_method_manual_in').id)
    company_id = fields.Many2one('res.company',  string='Công ty giao dịch',
                                 default=lambda self: self.env.company, )
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id')
    amount = fields.Monetary('Tổng tiền', tracking=True, help="Số tiền chi trả cho cộng tác viên")
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    collaborator_amount_vnd = fields.Float('Tổng tiền bằng số',digits=(3, 0))
    collaborator_text_total = fields.Text('Tổng tiền bằng chữ')
    collaborator_payment_date = fields.Date('Ngày', default=lambda self: fields.Datetime.now(),
                                   help="Ngày chi trả tiền cho cộng tác viên")
    collaborator_communication = fields.Text('Nội dung giao dịch')
    collaborator_user = fields.Many2one('res.users', 'Người chi', default=lambda self: self.env.user)
    collaborator_journal_id = fields.Many2one('account.journal', 'Sổ nhật ký')
    state = fields.Selection([('draft', 'Nháp'), ('posted', 'Đã xác nhận'), ('cancelled', 'Đã hủy')], default='draft',
                             string="Trạng thái")
    check_collaborator = fields.Boolean('Check cộng tác viên', default=True)
    collaborator_payment_line = fields.One2many('collaborator.payment.line', 'collaborator_payment_id', 'Phiếu chi liên quan')
    internal_payment_type = fields.Selection(PAYMENT_TYPE, string='Loại giao dịch nội bộ', default='tai_don_vi')
    company_payment = fields.Many2one('res.company', string='Công ty ghi nợ')

    collaborator_payment_cancel_date = fields.Date('Ngày hủy', help="Ngày hủy phiếu")
    note_cancel = fields.Text('Nội dung hủy')
    collaborator_user_cancel = fields.Many2one('res.users', 'Người hủy')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('collaborator.payment.sequence',  sequence_date=self.collaborator_payment_date) or 'New'
        res = super(CollaboratorPayment, self).create(vals)
        return res

    @api.constrains('amount')
    def check_amount(self):
        for rec in self:
            if rec.collaborator_amount < rec.amount:
                raise ValidationError('Số tiền bạn nhập đã vượt quá số tiền hiện có của cộng tác viên!')
            if rec.amount <= 0:
                raise ValidationError('Tổng tiền phải lớn hơn 0')
    @api.onchange('amount')
    def onchange_amount(self):
        if self.amount and self.amount > 0:
            # neu currency là VND
            if self.currency_id == self.env.ref('base.VND'):
                self.collaborator_text_total = num2words(round(self.amount), lang='vi_VN') + " đồng"
                self.collaborator_amount_vnd = self.amount * 1
            # neu currency khác
            else:
                self.collaborator_text_total = num2words(round(self.collaborator_amount_vnd)) + " đồng"
        elif self.amount and self.amount < 0:
            raise ValidationError(
                _('Số tiền thanh toán không hợp lệ!'))
        else:
            self.collaborator_text_total = "Không đồng"

    @api.onchange('currency_id')
    def back_value(self):
        # quy đổi tiền về tiền việt
        self.collaborator_text_total = num2words(round(self.collaborator_amount_vnd), lang='vi_VN') + " đồng"

    @api.onchange('internal_payment_type')
    def onchange_internal_payment_type(self):
        if self.internal_payment_type == 'tai_don_vi':
            self.contract_id = False
            self.phone = False
            self.collaborator_amount = False
            # self.collaborator_id = False
            self.company_payment = False
        else:
            self.contract_id = False
            self.phone = False
            self.collaborator_amount = False
            self.collaborator_id = False
            self.company_payment = False

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        domain = []
        for rec in self:
            if rec.internal_payment_type == 'tai_don_vi':
                if rec.collaborator_id:
                    domain = [('collaborator_id', '=', rec.collaborator_id.id), ('state', 'in', ('effect','expired')), ('company_id', '=', rec.company_id.id)]
                    amount = rec.collaborator_id.account_ids.filtered(lambda fol: fol.company_id in rec.contract_id.company_id and fol.collaborator_id in rec.collaborator_id and fol.contract_id in rec.contract_id)
                    rec.collaborator_amount = amount.amount_remain
                return {'domain': {'contract_id': domain}}
            else:
                if rec.collaborator_id:
                    domain = [('collaborator_id', '=', rec.collaborator_id.id), ('state', 'in', ('effect','expired')), ('company_id', '!=', rec.company_id.id)]
                    amount = rec.collaborator_id.account_ids.filtered(lambda fol: fol.company_id in rec.contract_id.company_id and fol.collaborator_id in rec.collaborator_id and fol.contract_id in rec.contract_id)
                    rec.collaborator_amount = amount.amount_remain
                    rec.company_payment = rec.contract_id.company_id
                return {'domain': {'contract_id': domain}}


    @api.onchange('collaborator_id')
    def onchange_collaborator_id(self):
        for rec in self:
            if rec.internal_payment_type == 'chi_ho':
                # check_contract = self.env['collaborator.contract'].search(
                #     [('collaborator_id', '=', self.collaborator_id.id), ('state', '=', 'effect')])
                # if check_contract:
                #     self.company_payment = check_contract[0].company_id
                #     if rec.company_payment:
                #         # rec.partner_id = rec.collaborator_id.partner_id
                #         rec.contract_id = rec.collaborator_id.contract_ids.filtered(lambda fol: fol.state in 'effect' and fol.collaborator_id in rec.collaborator_id and fol.company_id in rec.company_payment)
                #         amount = rec.collaborator_id.account_ids.filtered(lambda fol: fol.company_id in rec.contract_id.company_id and fol.collaborator_id in rec.collaborator_id and fol.contract_id in rec.contract_id)
                #         rec.collaborator_amount = amount.amount_remain
                #         rec.phone = rec.collaborator_id.phone
                contract_confrm = rec.collaborator_id.contract_ids.filtered(lambda fol: fol.state in 'effect' and fol.collaborator_id in rec.collaborator_id and fol.company_id not in rec.company_id)
                contract_exp = rec.collaborator_id.contract_ids.filtered(lambda fol: fol.state in 'expired' and fol.collaborator_id in rec.collaborator_id and fol.company_id not in rec.company_id)
                rec.company_payment = contract_confrm[0].company_id if contract_confrm else contract_exp[0].company_id if contract_exp else False
                contract_effect = rec.collaborator_id.contract_ids.filtered(lambda fol: fol.state in 'effect' and fol.collaborator_id in rec.collaborator_id and fol.company_id in rec.company_payment)
                contract_exp = rec.collaborator_id.contract_ids.filtered(lambda fol: fol.state in 'expired' and fol.collaborator_id in rec.collaborator_id and fol.company_id in rec.company_payment)
                rec.contract_id = contract_effect[0] if contract_effect else contract_exp[0] if contract_exp else False
                amount = rec.collaborator_id.account_ids.filtered(lambda fol: fol.company_id in rec.contract_id.company_id and fol.collaborator_id in rec.collaborator_id and fol.contract_id in rec.contract_id)
                rec.collaborator_amount = amount.amount_remain
                rec.phone = rec.collaborator_id.phone

            else:
                if rec.collaborator_id:
                    # rec.partner_id = rec.collaborator_id.partner_id
                    contract_effect = rec.collaborator_id.contract_ids.filtered(lambda fol: fol.state in 'effect' and fol.collaborator_id in rec.collaborator_id and fol.company_id in rec.company_id)
                    contract_exp = rec.collaborator_id.contract_ids.filtered(lambda fol: fol.state in 'expired' and fol.collaborator_id in rec.collaborator_id and fol.company_id in rec.company_id)
                    # rec.contract_id = contract_effect[0] if contract_effect else contract_exp[0] if contract_exp else False
                    if contract_effect:
                        rec.contract_id = contract_effect[0]
                    else:
                        if contract_exp:
                            rec.contract_id = contract_exp[0]
                        else:
                            rec.contract_id = False
                            domain = [('collaborator_id', '=', rec.collaborator_id.id),('state', 'in', ('effect', 'expired')), ('company_id', '=', rec.company_id.id)]
                            return {'domain': {'contract_id': domain}}
                    # rec.contract_id = rec.collaborator_id.contract_ids.filtered(lambda fol: fol.state in 'effect' and fol.collaborator_id in rec.collaborator_id and fol.company_id in rec.company_id)
                    amount = rec.collaborator_id.account_ids.filtered(lambda fol: fol.company_id in rec.contract_id.company_id and fol.collaborator_id in rec.collaborator_id and fol.contract_id in rec.contract_id)
                    rec.collaborator_amount = amount.amount_remain
                    rec.phone = rec.collaborator_id.phone

    # @api.onchange('company_id', 'collaborator_id')
    # def onchange_company_id(self):
    #     for rec in self:
    #         if rec.collaborator_id:
    #             # rec.partner_id = rec.collaborator_id.partner_id
    #             rec.contract_id = rec.collaborator_id.contract_ids.filtered(lambda fol: fol.state in 'effect' and fol.collaborator_id in rec.collaborator_id and fol.company_id in rec.company_id)
    #             amount = rec.collaborator_id.account_ids.filtered(lambda fol: fol.company_id in rec.company_id and fol.collaborator_id in rec.collaborator_id)
    #             rec.collaborator_amount = amount.amount_remain
    #             rec.phone = rec.collaborator_id.phone
    #         if rec.collaborator_id and rec.company_id:
    #             # rec.partner_id = rec.collaborator_id.partner_id
    #             rec.contract_id = rec.collaborator_id.contract_ids.filtered(lambda fol: fol.state in 'effect' and fol.collaborator_id in rec.collaborator_id and fol.company_id in rec.company_id)
    #             amount = rec.collaborator_id.account_ids.filtered(lambda fol: fol.company_id in rec.company_id and fol.collaborator_id in rec.collaborator_id)
    #             rec.collaborator_amount = amount.amount_remain
    #             rec.phone = rec.collaborator_id.phone

    def cancel_payment(self):
        return {
            'name': 'Thông tin hủy phiếu thanh toán',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('collaborator.collaborator_cancel_payment_wizard').id,
            'res_model': 'collaborator.cancel.payment.wizard',
            'context': {
                'default_collaborator_id': self.collaborator_id.id,
                'default_collaborator_payment': self.id,
                'default_contract_id': self.contract_id.id,
                'default_company_id': self.company_id.id,
                'default_company_payment': self.company_payment.id if self.company_payment else False,
                'default_brand_id': self.brand_id.id,
                'default_amount': self.amount,
            },
            'target': 'new',
        }

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_('Bạn chỉ có thể xoá khi ở trạng thái nháp, nếu có thể bạn hãy lưu trữ!'))
        return super(CollaboratorPayment, self).unlink()

    def post(self):
        for rec in self:
            payment = rec.collaborator_id.account_ids.filtered(lambda fol: fol.company_id in rec.contract_id.company_id and fol.collaborator_id in rec.collaborator_id and fol.contract_id in rec.contract_id)
            amount = payment.amount_remain
            if rec.amount > amount:
                raise ValidationError('Số tiền bạn nhập đã vượt quá số tiền hiện có của cộng tác viên!')
            else:
                if rec.company_payment:
                    total_collaborator = rec.collaborator_amount - rec.amount
                    amount = rec.collaborator_id.account_ids.filtered(lambda fol: fol.company_id in rec.company_payment and fol.collaborator_id in rec.collaborator_id)
                    amount.amount_remain = total_collaborator
                    amount.amount_used = amount.amount_used + rec.amount
                else:
                    total_collaborator = rec.collaborator_amount - rec.amount
                    amount = rec.collaborator_id.account_ids.filtered(lambda fol: fol.company_id in rec.company_id and fol.collaborator_id in rec.collaborator_id)
                    amount.amount_remain = total_collaborator
                    amount.amount_used = amount.amount_used + rec.amount
                rec.write({'state': 'posted'})

            # payment_id = rec.env['account.payment'].sudo().create({
            #     'payment_type': 'outbound',
            #     'payment_method': 'tm' if rec.collaborator_payment_method == 'tm' else 'ck',
            #     'partner_type': 'customer',
            #     'amount': rec.amount,
            #     'payment_date': rec.collaborator_payment_date,
            #     'communication': rec.collaborator_communication,
            #     'user': rec.collaborator_user.id,
            #     'journal_id': rec.collaborator_journal_id.id,
            #     'payment_method_id': rec.payment_method_id.id,
            # })
            # payment_collaborator = rec.env['collaborator.payment.line'].sudo().create({
            #     'collaborator_payment_id': rec.id,
            #     'payment_id': payment_id.id
            # })
            #
            # payment_id.post()

            # bỏ
            # payment = rec.env['account.payment'].sudo().create({
            #     'payment_type': 'outpay',
            #     'payment_method': 'tm' if rec.collaborator_payment_method == 'tm' else 'ck',
            #     'partner_type': 'customer',
            #     'amount': rec.amount,
            #     'payment_date': rec.collaborator_payment_date,
            #     'communication': rec.collaborator_communication,
            #     'user': rec.collaborator_user.id,
            #     'journal_id': rec.collaborator_journal_id.id,
            #     'payment_method_id': rec.payment_method_id.id,
            #     'payment_collaborator': rec.id,
            # })
            # payment.post()


class CollaboratorPaymentLine(models.Model):
    _name = 'collaborator.payment.line'
    _description = 'Dòng phiếu chi CTV'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    collaborator_payment_id = fields.Many2one('collaborator.payment', string="Phiếu chi cộng tác viên")
    # payment_id = fields.Many2one('account.payment', 'Phiếu chi và Bút toán liên quan')

