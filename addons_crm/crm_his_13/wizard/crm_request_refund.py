from odoo import models, fields, api
from odoo.exceptions import ValidationError
import datetime


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


class CRMRequestRefund(models.TransientModel):
    _name = 'crm.request.refund'
    _description = 'Biểu mẫu tạo phiếu hoàn tiền'
    _inherit = 'money.mixin'

    name = fields.Char('Lý do hoàn tiền')
    booking_id = fields.Many2one('crm.lead', string='Lead/Booking')
    partner_id = fields.Many2one('res.partner', string='Khách hàng')
    amount = fields.Monetary('Số tiền đặt cọc')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ')
    company_id = fields.Many2one('res.company', string='Chi nhánh thụ hưởng')
    journal_id = fields.Many2one('account.journal', string='Sổ nhật ký', domain="[('company_id', '=', company_id), ('type', 'in', ['cash', 'bank'])]")

    def convert_payment(self):
        if not self.company_id:
            raise ValidationError('Bạn chưa chọn chi nhánh thụ hưởng!!!')
        if self.amount <= 0:
            raise ValidationError('Nhập số tiền không đúng')
        else:
            payment = self.env['account.payment'].sudo().create({
                'is_deposit': True,
                'partner_id': self.partner_id.id,
                'company_id': self.company_id.id,
                'crm_id': self.booking_id.id or False,
                'currency_id': self.currency_id.id,
                'amount': self.amount,
                'brand_id': self.company_id.brand_id.id,
                'communication': self.name,
                'text_total': self.num2words_vnm(int(self.amount)) + " đồng",
                'partner_type': 'customer',
                'payment_type': 'outbound',
                'payment_date': datetime.datetime.now(),  # ngày thanh toán
                'date_requested': datetime.datetime.now(),  # ngày yêu cầu
                'payment_method_id': self.env['account.payment.method'].sudo().with_user(1).search(
                    [('payment_type', '=', 'inbound')], limit=1).id,
                # 'payment_method': 'tm',
                'journal_id': self.journal_id.id,
            })
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = 'Tạo phiếu hoàn tiền thành công!!'
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