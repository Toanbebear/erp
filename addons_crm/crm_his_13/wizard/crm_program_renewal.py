from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class CRMProgramRenewal(models.TransientModel):
    _name = 'crm.program.renewal'
    _description = 'CRM program renewal'

    brand_id = fields.Many2one('res.brand', string='Thương hiệu')
    campaign_id = fields.Many2one('utm.campaign', string='Chiến dịch', domain="[('brand_id', '=', brand_id)]")
    coupon_id = fields.Many2one('crm.discount.program', string='Coupon')
    name = fields.Char('Tên coupon mới')

    def action_program_renewal(self):
        if self.campaign_id.brand_id != self.coupon_id.brand_id:
            raise ValidationError('Bạn không thể gia hạn Coupon với chiến dịch của thương hiệu khác')
        else:
            if self.name:
                name = self.name
            else:
                name = 'GIA HẠN - ' + self.coupon_id.name
            coupon = self.env['crm.discount.program'].create({
                'name': name,
                'company_ids': [(6, 0, self.coupon_id.company_ids.ids)],
                'campaign_id': self.campaign_id.id,
                'brand_id': self.coupon_id.brand_id.id,
                'coupon_type': self.coupon_id.coupon_type,
                'start_date': self.campaign_id.start_date,
                'end_date': self.campaign_id.end_date,
            })
            for record in self.coupon_id.discount_program_list:
                coupon_detail = self.env['crm.discount.program.list'].create({
                    'discount_program': coupon.id,
                    'type_product': record.type_product,
                    'product_ids': [(6, 0, record.product_ids.ids)],
                    'product_ctg_ids': [(6, 0, record.product_ctg_ids.ids)],
                    'index': record.index,
                    'used': record.used,
                    'incremental': record.incremental,

                    'not_incremental_coupon': record.not_incremental_coupon,
                    'gift': record.gift,
                    'required_combo': record.required_combo,
                    'dc_min_qty': record.dc_min_qty,
                    'dc_max_qty': record.dc_max_qty,
                    'type_discount': record.type_discount,
                    'discount': record.discount,
                    'discount_bonus': record.discount_bonus,
                    'combo_note': record.combo_note
                })
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = 'Gia hạn coupon thành công!!'
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