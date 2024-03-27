from odoo import fields, api, models
from odoo.exceptions import ValidationError


# def num2words_vnm(num):
#     under_20 = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'mười một',
#                 'mười hai', 'mười ba', 'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín']
#     tens = ['hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']
#     above_100 = {100: 'trăm', 1000: 'nghìn', 1000000: 'triệu', 1000000000: 'tỉ'}
#
#     if num < 20:
#         return under_20[num]
#
#     elif num < 100:
#         under_20[1], under_20[5] = 'mốt', 'lăm'  # thay cho một, năm
#         result = tens[num // 10 - 2]
#         if num % 10 > 0:  # nếu num chia 10 có số dư > 0 mới thêm ' ' và số đơn vị
#             result += ' ' + under_20[num % 10]
#         return result
#
#     else:
#         unit = max([key for key in above_100.keys() if key <= num])
#         result = num2words_vnm(num // unit) + ' ' + above_100[unit]
#         if num % unit != 0:
#             if num > 1000 and num % unit < unit / 10:
#                 result += ' không trăm'
#             if 1 < num % unit < 10:
#                 result += ' linh'
#             result += ' ' + num2words_vnm(num % unit)
#     return result.capitalize()


class RequestDeposit(models.Model):
    _name = 'crm.request.deposit'
    _description = 'Phiếu cọc sang phiếu thu/hoàn tiền'
    _inherit = 'money.mixin'

    name = fields.Char('Nội dung giao dịch')
    booking_id = fields.Many2one('crm.lead', string='Lead/booking')
    partner_id = fields.Many2one('res.partner', string='Khách hàng')
    amount = fields.Monetary('Số tiền')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ')
    brand_id = fields.Many2one('res.brand', string='Thương hiệu')
    company_id = fields.Many2one('res.company', string='Chi nhánh thực hiện')
    payment_id = fields.Many2one('account.payment', string='Payment tương ứng')
    payment_date = fields.Date('Ngày')
    note = fields.Text("Ghi chú")
    coupon_id = fields.Many2one('crm.discount.program', string='Coupon', domain="[('brand_id', '=', brand_id)]")
    journal_id = fields.Many2one('account.journal', string='Sổ nhật ký')
    payment_method = fields.Selection(
        [('tm', 'Tiền mặt'), ('ck', 'Chuyển khoản'), ('nb', 'Thanh toán nội bộ'), ('pos', 'Quẹt thẻ qua POS'),
         ('vdt', 'Thanh toán qua ví điện tử')], string='Phương thức thanh toán')
    payment_type = fields.Selection([('inbound', 'Thu tiền'), ('outbound', 'Hoàn tiền')], string='Loại thanh toán', default='inbound')

    @api.onchange('payment_method', 'company_id')
    def payment_method_onchange(self):
        method = ''
        if self.payment_method and self.company_id:
            if self.payment_method == 'tm':
                method = 'cash'
            elif self.payment_method in ['ck', 'pos', 'cdt']:
                method = 'bank'
            return {'domain': {'journal_id': [
                ('id', 'in', self.env['account.journal'].search(
                    [('company_id', '=', self.company_id.id), ('type', '=', method)]).ids)]}}

    # def convert_payment(self):
    #     if not self.company_id:
    #         raise ValidationError('Bạn chưa chọn chi nhánh thụ hưởng!!!')
    #     if self.amount <= 0:
    #         raise ValidationError('Số tiền đặt cọc phải lớn hơn 0')
    #     if not self.journal_id:
    #         raise ValidationError('Bạn cần chọn Sổ nhật ký')
    #     else:
    #         if self.campaign_id:
    #             # self.booking_id.kept_coupon = [(4, self.coupon_id.id)]
    #             self.booking_id.kept_campaign = [(4, self.campaign_id.id)]
    #         payment = self.env['account.payment'].sudo().create({
    #             'is_deposit': True,
    #             'partner_id': self.partner_id.id,
    #             'company_id': self.company_id.id,
    #             'crm_id': self.booking_id.id or False,
    #             # 'currency_id': self.company_id.currency_id.id,
    #             'currency_id': self.currency_id.id,
    #             'amount': self.amount,
    #             'brand_id': self.brand_id.id,
    #             # 'communication': self.env.context.get('communication', "Đặt cọc giữ chương trình"),
    #             'communication': self.name,
    #             'text_total': num2words_vnm(int(self.amount)) + " đồng",
    #             'partner_type': 'customer',
    #             'payment_type': 'inbound',
    #             'payment_date': self.payment_date,  # ngày thanh toán
    #             'date_requested': self.payment_date,  # ngày yêu cầu
    #             'payment_method_id': self.env['account.payment.method'].sudo().with_user(1).search(
    #                 [('payment_type', '=', 'inbound')], limit=1).id,
    #             'payment_method': self.payment_method,
    #             'journal_id': self.journal_id.id,
    #         })
    #         # return {
    #         #     'name': 'Payment đặt cọc',
    #         #     'type': 'ir.actions.act_window',
    #         #     'view_type': 'form',
    #         #     'view_mode': 'form',
    #         #     'res_id': payment.id,
    #         #     'view_id': self.env.ref('account.view_account_payment_form').id,
    #         #     'res_model': 'account.payment',
    #         #     'context': {},
    #         # }
    #         view = self.env.ref('sh_message.sh_message_wizard')
    #         view_id = view and view.id or False
    #         context = dict(self._context or {})
    #         context['message'] = 'Tạo phiếu đặt cọc thành công!!'
    #         return {
    #             'name': 'Success',
    #             'type': 'ir.actions.act_window',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'sh.message.wizard',
    #             'views': [(view_id, 'form')],
    #             'view_id': view.id,
    #             'target': 'new',
    #             'context': context,
    #         }

    def convert_payment(self):
        if self.payment_type == 'outbound' and self.amount >= self.booking_id.amount_remain:
            raise ValidationError('Khách hàng không đủ tiền để hoàn. \nSố tiền có thể hoàn là %sđ' %'{0:,.0f}'.format(self.booking_id.amount_remain))
        payment_type = 'inbound'
        is_deposit = True
        if self.payment_type == 'outbound':
            payment_type = 'outbound'
            is_deposit = False
        self.env['account.payment'].sudo().create({
            'is_deposit': is_deposit,
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'crm_id': self.booking_id.id or False,
            'currency_id': self.currency_id.id,
            'amount': self.amount,
            'brand_id': self.brand_id.id,
            # 'communication': self.env.context.get('communication', "Đặt cọc giữ chương trình"),
            'communication': self.name,
            'text_total': self.num2words_vnm(int(self.amount)) + " đồng",
            'partner_type': 'customer',
            'payment_type': payment_type,
            'payment_date': self.payment_date,
            'date_requested': self.payment_date,
            'payment_method_id': self.env['account.payment.method'].sudo().with_user(1).search(
                [('payment_type', '=', 'inbound')], limit=1).id,
            'payment_method': self.payment_method,
            'journal_id': self.journal_id.id,
        })
        if self.campaign_id:
            self.booking_id.kept_campaign = [(4, self.campaign_id.id)]

        # return {
        #     'name': 'Payment đặt cọc',
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_id': payment.id,
        #     'view_id': self.env.ref('account.view_account_payment_form').id,
        #     'res_model': 'account.payment',
        #     'context': {},
        # }
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = 'Tạo phiếu đặt cọc thành công!!'
        return {
            'name': 'Thông báo thành công',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view_id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }
