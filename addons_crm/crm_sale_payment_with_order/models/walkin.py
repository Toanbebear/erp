from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
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


class WalkinSalePaymentWithSO(models.Model):
    _inherit = "sh.medical.appointment.register.walkin"
    def create_draft_payment(self):
        self.ensure_one()

        if self.service:
            # tính toán tổng tiền còn thiếu của từng so line
            order = self.sudo().sale_order_id

            draft_payment = False
            service_name = ''
            for ser in self.service:
                service_name += ser.name + ";"

            if self.payment_ids:
                draft_payment = self.sudo().payment_ids.search(
                    [('id', 'in', self.sudo().payment_ids.ids), ('state', '=', 'draft'),
                     ('payment_type', '=', 'inbound')], limit=1)
            if draft_payment:  # nếu có phiếu nháp thì chỉnh tiền và ghi chú ở phiếu nháp
                draft_payment = draft_payment.sudo()
                draft_payment.amount = order.amount_missing_money()  # Số tiền cần thanh toán
                draft_payment.text_total = self.num2words_vnm(int(order.amount_missing_money())) + " đồng"
                draft_payment.communication = "Thu phí dịch vụ: " + service_name
                draft_payment.payment_date = fields.Date.today()
                draft_payment.date_requested = fields.Date.today()

            else:  # tạo mới nếu ko coa payment nháp
                journal_id = self.env['account.journal'].search(
                    [('type', '=', 'cash'), ('company_id', '=', self.env.company.id)], limit=1)
                self.env['account.payment'].create({
                    'name': False,
                    'partner_id': self.patient.partner_id.id,
                    'patient': self.patient.id,
                    'company_id': self.env.company.id,
                    'currency_id': self.env.company.currency_id.id,
                    'amount': order.amount_missing_money(),
                    'brand_id': self.booking_id.brand_id.id,
                    'crm_id': self.booking_id.id,
                    'communication': "Thu phí dịch vụ: " + service_name,
                    'text_total': self.num2words_vnm(int(order.amount_missing_money())) + " đồng",
                    'partner_type': 'customer',
                    'payment_type': 'inbound',
                    'payment_date': datetime.date.today(),  # ngày thanh toán
                    'date_requested': datetime.date.today(),  # ngày yêu cầu
                    'payment_method_id': self.env['account.payment.method'].sudo().search(
                        [('payment_type', '=', 'inbound')], limit=1).id,
                    'journal_id': journal_id.id,
                    'walkin': self.id,
                })
            self.write({'state': 'WaitPayment'})  # chuyển trạng thái phiếu về chờ thanh toán

        else:
            raise ValidationError('You must select at least one service!')

    @api.depends('sale_order_id.amount_total', 'sale_order_id.amount_remain', 'sale_order_id.amount_remain', 'sale_order_id.order_line.price_subtotal', 'sale_order_id.order_line.amount_remain')
    def _check_missing_money(self):
        for record in self.with_env(self.env(su=True)):
            order = record.sale_order_id
            record.is_missing_money = True
            if not order.check_order_missing_money():
                if (record.state not in ['WaitPayment','Completed']) and (record.sale_order_id.state in ['draft','sent']) and (record.sale_order_id.amount_total > 0) \
                        and (record.sale_order_id.amount_total > (record.sale_order_id.amount_remain + record.sale_order_id.amount_owed)):
                    record.is_missing_money = True
                else:
                    if record.state in ['Scheduled']:
                        record.set_to_progress()
                    record.is_missing_money = False
