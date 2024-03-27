from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


class InheritApplyCouponType6(models.TransientModel):
    _inherit = 'crm.apply.coupon'
    _description = 'Inherit Apply Coupon Type 6'

    def cart_class_coupon(self):
        loyalty_id = self.crm_id.loyalty_id
        if loyalty_id:
            if loyalty_id.rank_id == self.coupon_id.rank_id:
                for line in self.line_ids:
                    for discount in self.coupon_id.discount_program_list:
                        if self.check_crm_line(discount, line) is True:
                            self.apply_discount(discount, line)
            else:
                raise ValidationError('Khách hàng không thuộc hạng thẻ được áp dụng')
        else:
            raise ValidationError('Khách hàng chưa có hạng thẻ')




