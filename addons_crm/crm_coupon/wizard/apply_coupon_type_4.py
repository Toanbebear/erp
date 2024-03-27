from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
import itertools


class InheritApplyCouponType4(models.TransientModel):
    _inherit = 'crm.apply.coupon'
    _description = 'Inherit Apply Coupon Type 4'

    def treatment_coupon(self):
        self.get_index()
        index = self.index
        for line in self.line_ids:
            quantity_temp = 0
            for discount in self.coupon_id.discount_program_list:
                if self.check_crm_line(discount, line) is True:
                    if discount.index == index and line.quantity + quantity_temp > discount.dc_max_qty:
                        quantity = discount.dc_max_qty - discount.dc_min_qty + 1
                        if line.quantity == 1:
                            self.apply_discount(discount, line)
                            break
                        else:
                            crm_line = self.clone_crm_line(line, quantity)
                            self.apply_discount(discount, crm_line)
                            quantity_temp += quantity
                            line.quantity -= quantity
                    elif discount.index == index and line.quantity <= discount.dc_max_qty:
                        self.apply_discount(discount, line)
                        break

    def clone_crm_line(self, line, quantity):
        crm_line = self.env['crm.line'].create({
            'name': line.name,
            'service_id': line.service_id.id,
            'quantity': quantity,
            'unit_price': line.unit_price,
            'price_list_id': line.price_list_id.id,
            'company_id': line.company_id.id,
            # 'prg_ids': [(4, self.coupon_id.id)],
            'source_extend_id': self.crm_id.source_id.id,
            'crm_id': self.crm_id.id,
            'product_id': line.product_id.id,
            'is_treatment': line.is_treatment,
            'consultants_1': line.consultants_1.id,
            'consultants_2': line.consultants_2.id,
            'consulting_role_1': line.consulting_role_1,
            'consulting_role_2': line.consulting_role_2,
        })
        return crm_line

    def list_treatment_combo(self):
        list_indexs = []
        list_remove = []
        for line in self.line_ids:
            for discount in self.coupon_id.discount_program_list:
                if self.check_crm_line(discount, line) is True:
                    if self.check_quantity(discount, line) is True and self.check_required_combo(discount) is True:
                        list_indexs.append(discount.index)
                    if discount.required_combo is True and line.quantity < discount.dc_min_qty:
                        list_remove.append(discount.index)
        new_list = [index for index in list_indexs if index not in list_remove]
        return new_list








