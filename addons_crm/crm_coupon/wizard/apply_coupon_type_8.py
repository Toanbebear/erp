from odoo import fields, models, api, _


class InheritApplyCouponType8(models.TransientModel):
    _inherit = 'crm.apply.coupon'
    _description = 'Inherit Apply Coupon Type 8'

    def check_list_product_used(self, discount):
        sale_order = self.env['sale.order.line'].search([('order_partner_id', '=', self.partner_id.id)]).product_id
        used_list = []
        for rec in sale_order:
            used_list.append(rec.default_code)
        check = False
        if discount.type_product_used == 'product_ctg':
            category_ids = discount.product_ctg_used_ids
            service_ids = self.env['sh.medical.health.center.service'].search([])
            code_list = []
            for ser in service_ids:
                if ser.service_category in category_ids:
                    code_list.append(ser.default_code)
            if len(set(used_list) & set(code_list)) > 0:
                check = True
        else:
            code_list = []
            for rec in discount.product_used_ids:
                code_list.append(rec.default_code)
            if len(set(code_list) & set(used_list)) > 0:
                check = True
        return check

    def used_service_coupon(self):
        for line in self.line_ids:
            for discount in self.coupon_id.discount_program_list:
                if self.check_crm_line(discount, line) is True:
                    if self.check_list_product_used(discount) is True:
                        self.apply_discount(discount, line)
