from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


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


class SellVoucher(models.Model):
    _name = 'sell.voucher'
    _description = 'Sell Voucher'
    _rec_name = 'voucher_program_id'
    _inherit = 'money.mixin'
    brand_id = fields.Many2one('res.brand', string='Brand')
    voucher_program_id = fields.Many2one('crm.voucher.program', string='Voucher Program',
                                         domain="[('brand_id','=',brand_id), ('stage_prg_voucher','=', 'active')]")
    voucher_ids = fields.One2many('crm.voucher', 'sell_voucher_id', string='Voucher')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', string='Customer')
    currency_id = fields.Many2one('res.currency', string='Currency', related='voucher_program_id.currency_id',
                                  store=True)
    unit_price = fields.Monetary(string='Unit Price', related='voucher_program_id.price', store=True, digit=(3, 0))
    quantity = fields.Integer('Quantity', default=1)
    total = fields.Monetary('Total', compute='_get_total', store=True, digit=(3, 0))
    check_payment = fields.Boolean('Check payment', compute='get_check_payment', store=True)
    payment_id = fields.Many2one('account.payment', string='Payment')
    check_num_sold = fields.Boolean('check', compute='check_num_voucher_sold', store=True,
                                    help="Check the number of vouchers sold")

    @api.model
    def create(self, vals_list):
        res = super(SellVoucher, self).create(vals_list)
        res.product_id = self.env.ref('crm_base.voucher_product_data').id
        return res

    @api.depends('voucher_ids')
    def check_num_voucher_sold(self):
        for record in self:
            record.check_num_sold = False
            if record.voucher_ids:
                if record.quantity == len(record.voucher_ids):
                    record.check_num_sold = True

    @api.depends('unit_price', 'quantity')
    def _get_total(self):
        for record in self:
            record.total = 0
            if record.unit_price and record.quantity:
                record.total = record.unit_price * record.quantity

    @api.depends('payment_id.state')
    def get_check_payment(self):
        for record in self:
            record.check_payment = False
            if record.payment_id.state == 'posted' or not record.unit_price:
                record.check_payment = True

    @api.constrains('voucher_program_id', 'quantity')
    def constrain_quantity(self):
        for record in self:
            if record.voucher_program_id:
                voucher_active = self.env['crm.voucher'].search(
                    [('voucher_program_id', '=', record.voucher_program_id.id),
                     ('stage_voucher', 'in', ['new', 'active']),
                     ('partner_id', '=', False), ('partner2_id', '=', False)])
                if record.quantity > len(voucher_active):
                    raise ValidationError('Hiện tại chỉ có %s voucher khả dụng' % len(voucher_active))

    def create_payment(self):
        payment = self.env['account.payment'].sudo().create({
            'name': False,
            'payment_type': 'inbound',
            'partner_id': self.partner_id.id,
            'company_id': self.env.user.company_id.id,
            'currency_id': self.currency_id.id,
            'amount': self.total,
            'communication': "Thu phí voucher: " + self.voucher_program_id.name,
            'text_total': self.num2words_vnm(int(self.total)) + " đồng",
            'partner_type': 'customer',
            'payment_date': date.today(),
            'payment_method_id': '1',
            'journal_id': self.env['account.journal'].search(
                [('company_id', '=', self.env.user.company_id.id), ('type', '=', 'cash')], limit=1).id,
        })
        self.payment_id = payment.id
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = 'Phiếu thanh toán đã được tạo!!'
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

    def gift_voucher(self):
        if self.check_payment and self.check_num_sold:
            raise ValidationError('Đã bàn giao đủ số lượng voucher cho khách hàng')
        elif not self.check_payment:
            raise ValidationError('Khách hàng chưa thanh toán')
        else:
            price_list = self.env['product.pricelist'].search(
                [('brand_id', '=', self.brand_id.id), ('type', '=', 'product')], order='id desc', limit=1)
            order = self.env['sale.order'].sudo().create({
                'partner_id': self.partner_id.id,
                'pricelist_id': price_list.id,
                'company_id': self.env.user.company_id.id,
            })
            order_line = self.env['sale.order.line'].sudo().create({
                'order_id': order.id,
                'product_id': self.product_id.id,
                'product_uom': self.product_id.uom_id.id,
                'company_id': self.env.user.company_id.id,
                'price_unit': self.unit_price,
                'product_uom_qty': self.quantity,
                'tax_id': False,
            })
            order.action_confirm()
            vouchers = self.env['crm.voucher'].search(
                [('voucher_program_id', '=', self.voucher_program_id.id), ('stage_voucher', 'in', ['new', 'active']),
                 ('partner_id', '=', False)], limit=self.quantity)
            if vouchers:
                vouchers.write({'partner_id': self.partner_id.id})
                self.write({'voucher_ids': [(4, voucher.id) for voucher in vouchers]})
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = 'Ghi nhận bàn giao %s voucher!!' % len(vouchers)
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