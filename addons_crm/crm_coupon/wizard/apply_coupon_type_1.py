from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
import itertools


class InheritApplyCouponType1(models.TransientModel):
    _inherit = 'crm.apply.coupon'
    _description = 'Inherit Apply Coupon Type 1'

    # Hàm check điều kiện cho coupon đơn lẻ
    def check_coupon_type_1(self, lines, coupon_id):
        for discount_line in coupon_id.discount_program_list:
            if discount_line.gift:
                self.create_crm_line_gift(discount_line.product_ids, discount_line)
            else:
                if discount_line.type_product == 'product_ctg':
                    line_result = lines.filtered(
                        lambda l: (l.service_id.service_category in discount_line.product_ctg_ids) and (
                                self.coupon_id not in l.prg_ids))
                    quantity = 0
                    for line in line_result:
                        quantity += line.quantity * line.uom_price
                    if (quantity >= discount_line.dc_min_qty) and (quantity <= discount_line.dc_max_qty):
                        self.set_discount_coupon_1(line_result, discount_line)
                else:
                    line_result = lines.filtered(lambda l: (l.product_id in discount_line.product_ids) and (
                            self.coupon_id not in l.prg_ids))
                    quantity = 0
                    for line in line_result:
                        quantity += line.quantity * line.uom_price
                    if (quantity >= discount_line.dc_min_qty) and (quantity <= discount_line.dc_max_qty):
                        self.set_discount_coupon_1(line_result, discount_line)

    # Hàm set CTKM cho từng line dịch vụ
    def set_discount_coupon_1(self, line_result, discount_line):
        if discount_line.limit_discount < 1:
            raise ValidationError('Coupon đã hết lượt sử dụng, kiểm tra lại trong Coupon chi tiết')
        else:
            discount_line.limit_discount -= 1
        for line in line_result:
            discount_rec = line.prg_ids.mapped('discount_program_list')
            discounted = discount_rec.filtered(lambda d: (line.product_id in d.product_ids) or (
                    line.service_id.service_category in d.product_ctg_ids)).mapped('incremental')
            if (all(discounted) and discount_line.incremental) or (discount_line and not discount_rec):
                if not line.prg_ids or (
                        line.prg_ids and (
                        'sale_to' not in discount_line.mapped('type_discount')) and line.sale_to == 0):
                    if discount_line.type_discount == 'percent':
                        line.discount_percent += discount_line.discount
                    elif discount_line.type_discount == 'cash':
                        line.discount_cash += (discount_line.discount * line.quantity * line.uom_price)
                    else:
                        line.sale_to = discount_line.discount * line.quantity * line.uom_price
                    line.prg_ids = [(4, self.coupon_id.id)]
                    self.crm_id.prg_ids = [(4, self.coupon_id.id)]
                    discount_history = self.env['crm.line.discount.history'].create({
                        'booking_id': self.crm_id.id,
                        'crm_line': line.id,
                        'discount_program': self.coupon_id.id,
                        'index': 0,
                        'type': 'discount',
                        'type_discount': discount_line.type_discount,
                        'discount': discount_line.discount
                    })
                    if discount_line.type_discount in ['percent']:
                        discount_history.write({
                            'discount': discount_line.discount
                        })
                    elif discount_line.type_discount in ['cash', 'sale_to']:
                        discount_history.write({
                            'discount': discount_line.discount * line.quantity * line.uom_price
                        })
                    if line.stage == 'processing':
                        # Nếu line dv này có ở trạng thái đang xử lý cần sửa giá ở SO nữa
                        # order_id = self.env['sale.order'].search(
                        #     [('booking_id', '=', self.crm_id.id), ('state', '=', 'draft')])
                        # order_line_id = self.env['sale.order.line']
                        # if order_id:
                        #     order_line_ids = order_id.mapped('order_line')
                        #     order_line_id += order_line_ids.filtered(lambda l: l.crm_line_id == line)
                        #     if order_line_id and ((line.uom_price * line.quantity) != 0):
                        #         order_line_id.discount = line.discount_percent
                        #         order_line_id.discount_cash = line.discount_cash / (line.quantity * line.uom_price) * order_line_id.uom_price
                        #         order_line_id.sale_to = line.sale_to / (line.quantity * line.uom_price) * order_line_id.uom_price
                        self.update_sale_order(line)
                        # Nếu có payment dạng nháp cũng sửa luôn nữa
                        # walkin = self.env['sh.medical.appointment.register.walkin'].search(
                        #     [('sale_order_id', '=', order_line_id.id), ('state', 'in', ['Scheduled', 'WaitPayment'])])
                        # if walkin:
                        #     payment = self.env['account.payment'].search(
                        #         [('crm_id', '=', self.crm_id.id), ('walkin', '=', walkin.id),
                        #          ('state', '=', 'draft')])
                        #     if payment:
                        #         payment.amount = order_id.amount_total

    def create_crm_line_gift(self, product_id, discount_line):
        crm_line = self.env['crm.line'].create({
            'name': product_id.name,
            'product_id': product_id.id,
            'quantity': discount_line.gift,
            'unit_price': 0,
            'price_list_id': self.crm_id.price_list_id.id,
            'company_id': self.crm_id.company_id.id,
            'prg_ids': [(4, self.coupon_id.id)],
            'source_extend_id': self.crm_id.source_id.id,
        })
        self.env['crm.line.discount.history'].create({
            'booking_id': self.crm_id.id,
            'crm_line': crm_line.id,
            'discount_program': self.coupon_id.id,
            'index': discount_line.index,
            'type': 'gift',
        })
        self.crm_id.prg_ids = [(4, self.coupon_id.id)]
