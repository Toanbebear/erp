from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
import datetime
from datetime import timedelta


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


class CRMSaleOrder(models.Model):
    _inherit = 'sale.order'
    is_missing_money = fields.Boolean(string='Thiếu tiền thực hiện?', compute='_check_missing_money')

    @api.depends('amount_total', 'amount_remain', 'amount_owed', 'pricelist_type')
    def _check_missing_money(self):
        for record in self.with_env(self.env(su=True)):
            record.is_missing_money = False
            if (record.pricelist_type == 'product') and (record.amount_total > (record.amount_remain + record.amount_owed)):
                record.is_missing_money = True

    def action_cancel(self):
        res = super(CRMSaleOrder, self).action_cancel()
        if self.booking_id and self.pricelist_id.type == 'product':
            for record in self.order_line:
                if record.line_product:
                    record.line_product.stage_line_product = 'new'
                    record.line_product.order_line = False
        return res

    def action_confirm(self):
        self.ensure_one()
        if not self.sh_room_id and self.pricelist_type == 'product':
            raise ValidationError('Bạn cần chọn Phòng xuất hàng trước khi xác nhận.')
        # if ((self.amount_remain + self.amount_owed) < self.amount_total) and (self.pricelist_type == 'product'):
        if self.check_order_missing_money():
            raise ValidationError('Số tiền còn lại của khách hàng không đủ để thanh toán cho đơn hàng này')
        res = super(CRMSaleOrder, self).action_confirm()
        # Nếu đây là SO bán sản phẩm và đc tạo từ BK. Khi xác nhận SO sẽ xóa tất cả các line sản phẩm trên BK
        if self.booking_id and self.pricelist_type == 'product':
            # SO bán sản phẩm làm cho BK won nếu BK đang ở trạng thái đặt cọc và Số tiền còn lại của KH khác 0
            if (self.booking_id.stage_id == self.env.ref(
                    'crm_base.crm_stage_paid')) and self.booking_id.amount_remain == 0:
                self.booking_id.stage_id = self.env.ref('crm.stage_lead4').id
                self.booking_id.effect = 'expire'
                self.booking_id.booking_notification = "Booking hết hiệu lực. Bạn chỉ có thể tạo được phiếu khám từ Booking này."
            for record in self.order_line:
                if record.line_product:
                    record.line_product.stage_line_product = 'sold'
                    record.line_product.date_confirm_so = datetime.datetime.now()
        return res

    def request_payment(self):
        self.ensure_one()
        total_so = self.amount_total
        product_name = ''
        for record in self.order_line:
            product_name += record.product_id.name + "; "
        if not self.booking_id:
            raise ValidationError('Báo giá này chưa được gắn với Booking!!!')
        journal_id = self.env['account.journal'].search(
            [('type', '=', 'cash'), ('company_id', '=', self.env.company.id)], limit=1)
        payment = self.env['account.payment'].sudo().create({
            'name': False,
            'partner_id': self.partner_id.id,
            'company_id': self.env.company.id,
            'currency_id': self.env.company.currency_id.id,
            'amount': total_so,
            'brand_id': self.booking_id.brand_id.id,
            'crm_id': self.booking_id.id,
            'communication': "Thu phí đơn hàng: " + self.name + " : " + product_name,
            'text_total': self.num2words_vnm(int(total_so)) + " đồng",
            'partner_type': 'customer',
            'payment_type': 'inbound',
            'payment_date': datetime.date.today(),  # ngày thanh toán
            'date_requested': datetime.date.today(),  # ngày yêu cầu
            'payment_method_id': self.env['account.payment.method'].sudo().search(
                [('payment_type', '=', 'inbound')], limit=1).id,
            'journal_id': journal_id.id,
        })
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = 'Tạo phiếu thu nháp thành công!! \n Vui lòng liên hệ thu ngân xác nhận phiếu thu nháp vừa tạo.'
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


class CRMSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_product = fields.Many2one('crm.line.product', string='Dòng sản phẩm')
    consultants_1 = fields.Many2one('res.users', related='line_product.consultants_1')
    consultants_2 = fields.Many2one('res.users', related='line_product.consultants_2')

    @api.model
    def create(self, vals):
        res = super(CRMSaleOrderLine, self).create(vals)
        if res.product_id.type == 'product' and res.order_id and res.order_id.booking_id and not res.line_product:
            crm_line_product = self.env['crm.line.product'].create({
                'product_id': res.product_id.id,
                'product_uom_qty': res.product_uom_qty,
                'price_unit': res.price_unit,
                'booking_id': res.order_id.booking_id.id,
                'company_id': res.order_id.company_id.id,
                'source_extend_id': res.order_id.booking_id.source_id.id,
                'product_pricelist_id': res.order_id.pricelist_id.id,
                'stage_line_product': 'processing',
                'consultants_1': self.env.user.id
            })
            res.line_product = crm_line_product.id
        return res

    def write(self, vals):
        res = super(CRMSaleOrderLine, self).write(vals)
        for record in self:
            if vals.get('product_id') and record.line_product and record.order_id.pricelist_type == 'product':
                record.line_product.product_id = record.product_id.id
                record.line_product.price_unit = record.price_unit
            if vals.get('product_uom_qty') and record.line_product and record.order_id.pricelist_type == 'product':
                record.line_product.product_uom_qty = record.product_uom_qty
        return res

    def unlink(self):
        for record in self:
            if record.line_product and record.order_id.pricelist_type == 'product' and not record.crm_line_id:
                record.line_product.stage_line_product = 'new'
        return super(CRMSaleOrderLine, self).unlink()

