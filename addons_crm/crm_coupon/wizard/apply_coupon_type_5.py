from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


class InheritApplyCouponType5(models.TransientModel):
    _inherit = 'crm.apply.coupon'
    _description = 'Inherit Apply Coupon Type 5'

    group_customer_id = fields.Many2one('crm.group.customer', string='Mã chi tiết')

    def group_coupon(self):
        discount = self.group_customer_id.coupon_detail_id
        for line in self.line_ids:
            if self.check_crm_line(discount, line) is True and len(line.prg_ids) == 0:
                self.apply_discount(discount, line)
                self.group_customer_id.booking_ids += self.crm_id









