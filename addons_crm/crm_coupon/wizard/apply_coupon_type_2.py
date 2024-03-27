from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from itertools import zip_longest
from datetime import datetime, date
import itertools


class InheritApplyCouponType2(models.TransientModel):
    _inherit = 'crm.apply.coupon'
    _description = 'Inherit Apply Coupon Type 2'

    def bill_coupon(self):
        coupon_bill_ids = self.coupon_id.coupon_bill_ids.sorted(key=lambda r: r.total_min)[::-1]
        crm_line_ids = self.line_ids.sorted(key=lambda r: r.total)[::-1]
        bill_total = sum(self.line_ids.mapped('total'))
        if self.coupon_id.country_id and self.coupon_id.country_id.id != self.crm_id.country_id.id:
            raise ValidationError('Khách hàng nằm ngoài khu vực được áp dụng')
        if self.coupon_id.state_ids and self.crm_id.state_id.id not in self.coupon_id.state_ids.ids:
            raise ValidationError('Khách hàng nằm ngoài khu vực được áp dụng')
        if self.coupon_id.product_cate_ids:
            service = self.env['crm.line'].search([('crm_id', '=', self.crm_id.id), ('service_id.service_category.id', 'in', self.coupon_id.product_cate_ids.ids)])
            if len(service) == 0:
                raise ValidationError('Các dịch vụ không thuộc nhóm được áp dụng')
        if bill_total < coupon_bill_ids[-1].total_min:
            raise ValidationError('Tổng giá trị booking không đạt số tiền tối thiểu áp dụng coupon')
        for discount in coupon_bill_ids:
            if bill_total >= discount.total_min:
                self.apply_coupon_bill(discount, crm_line_ids)
                break

    def apply_coupon_bill(self, discount, line_ids):
        cash = discount.discount
        discount_cash = 0
        for line in line_ids:
            if len(line.prg_ids) == 0:
                deposit = self.env['crm.request.deposit'].search([('booking_id', '=', self.crm_id.id), ('coupon_id', '=', self.coupon_id.id)])
                if deposit:
                    for rec in deposit:
                        rec.used = True
                line.prg_ids += self.coupon_id
                self.crm_id.prg_ids += self.coupon_id
                if discount.type_discount == 'percent':
                    line.discount_percent += discount.discount
                elif discount.type_discount == 'cash':
                    if line.total < cash:
                        discount_cash = line.total
                        cash -= discount_cash
                    else:
                        discount_cash = cash
                        cash = 0
                    line.discount_cash += discount_cash
                self.create_history(discount, line, discount_cash)
                self.update_sale_order(line)
