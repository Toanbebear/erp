from odoo import fields, api, models


class CRMBooking(models.Model):
    _inherit = 'crm.lead'

    def apply_coupon(self):
        crm_line_ids = []
        for crm_line in self.crm_line_ids:
            if (crm_line.stage in ['new', 'processing']) and (crm_line.number_used == 0):
                crm_line_ids.append(crm_line.id)
        crm_line_product_ids = []
        for crm_line_product in self.crm_line_product_ids:
            if crm_line_product.stage_line_product in ['new', 'processing']:
                crm_line_product_ids.append(crm_line_product.id)

        wizard_form = self.env.ref('crm_coupon.view_apply_coupon', False)
        view_id = self.env['crm.apply.coupon']
        # vals = {
        #     'partner_id': self.partner_id.id,
        #     'crm_id': self.id,
        #     'line_ids': [(6, 0, crm_line_ids)],
        #     'type_coupon': '1'
        # }
        # new = view_id.create(vals)
        return {
            'name': 'Áp dụng coupon',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.apply.coupon',
            # 'res_id': new.id,
            'view_id': wizard_form.id,
            'view_type': 'form',
            'view_mode': 'form',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_crm_id': self.id,
                'default_type_action': 'apply',
                'default_type_coupon': '1',
                'default_line_ids': [(6, 0, crm_line_ids)],
                'default_line_product_ids': [(6, 0, crm_line_product_ids)],
            },
            'target': 'new'
        }

    def apply_coupon_new(self):
        crm_line_ids = []
        for crm_line in self.crm_line_ids:
            if (crm_line.stage in ['new', 'processing']) and (crm_line.number_used == 0):
                crm_line_ids.append(crm_line.id)
        crm_line_product_ids = []
        for crm_line_product in self.crm_line_product_ids:
            if crm_line_product.stage_line_product in ['new', 'processing']:
                crm_line_product_ids.append(crm_line_product.id)

        wizard_form = self.env.ref('crm_coupon.view_apply_coupon_new', False)
        view_id = self.env['crm.apply.coupon']
        # vals = {
        #     'partner_id': self.partner_id.id,
        #     'crm_id': self.id,
        #     'line_ids': [(6, 0, crm_line_ids)],
        #     'type_coupon': '1'
        # }
        # new = view_id.create(vals)
        return {
            'name': 'Áp dụng coupon',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.apply.coupon',
            # 'res_id': new.id,
            'view_id': wizard_form.id,
            'view_type': 'form',
            'view_mode': 'form',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_crm_id': self.id,
                'default_type_action': 'apply',
                'default_type_coupon': '1',
                'default_line_ids': [(6, 0, crm_line_ids)],
                'default_line_product_ids': [(6, 0, crm_line_product_ids)],
            },
            'target': 'new'
        }



    def create_coupon_group(self):
        return {
            'name': 'Create coupon group',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_coupon.group_customer_form_view').id,
            'res_model': 'crm.group.customer',
            'target': 'new',
        }
