from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


class InheritApplyCouponType7(models.TransientModel):
    _inherit = 'crm.apply.coupon'
    _description = 'Inherit Apply Coupon Type 7'

    def old_new_customers_coupon(self):
        if self.partner_id.type_data_partner != self.coupon_id.type_data_partner:
            if self.coupon_id.type_data_partner == 'old':
                raise ValidationError('Coupon chỉ áp dụng cho khách hàng cũ')
            else:
                raise ValidationError('Coupon chỉ áp dụng cho khách hàng mới')
        else:
            for line in self.line_ids:
                for discount in self.coupon_id.discount_program_list:
                    if self.check_crm_line(discount, line) is True:
                        self.apply_discount(discount, line)
