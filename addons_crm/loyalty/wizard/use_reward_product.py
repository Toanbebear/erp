import datetime

from odoo import fields, models, api


class CrmLoyaltyUseReward(models.TransientModel):
    _name = 'crm.loyalty.use.reward'
    _description = 'Crm Loyalty Use Reward'

    def domain_product(self):
        reward = self.env['crm.loyalty.line.reward'].sudo().browse(self._context.get('default_reward_id'))
        return [('id', 'in', reward.product_ids.ids)]

    loyalty_id = fields.Many2one('crm.loyalty.card', string='Loyalty')
    brand_id = fields.Many2one('res.brand')
    pricelist_id = fields.Many2one('product.pricelist', string='Bảng giá')
    reward_id = fields.Many2one('crm.loyalty.line.reward', string='Reward')
    booking_id = fields.Many2one('crm.lead', string='Booking')
    partner_id = fields.Many2one('res.partner', string='Customer')
    product_id = fields.Many2one('product.product', string='Sản phẩm', domain=domain_product)
    product_ids = fields.Many2many('product.product', string='Sản phẩm', compute='get_product_id')
    type = fields.Selection([('prd', 'Sản phẩm'),('ctg', 'Category Product'),('service', 'Dịch vụ')], string='Loại', compute='set_type')

    @api.depends('reward_id')
    def get_product_id(self):
        for rec in self:
            if rec.reward_id and rec.reward_id.product_ids:
                rec.write({'product_ids': [(6, 0, rec.reward_id.product_ids.ids)]})

    @api.depends('reward_id.type_reward')
    def set_type(self):
        for rec in self:
            if rec.reward_id.type_reward:
                rec.type = rec.reward_id.type_reward

    def confirm(self):
        self.reward_id.stage = 'processing'
        line = self.env['crm.line']
        line_product = self.env['crm.line.product']
        if self.reward_id.type_reward in ['service', 'ctg']:
            pricelist_item = self.env['product.pricelist.item'].sudo().search(
                [('pricelist_id', '=', self.pricelist_id.id),
                 ('product_id', '=', self.product_id.id)], limit=1)
            line += self.env['crm.line'].sudo().create({
                'name': self.reward_id.name,
                'product_id': self.product_id.id,
                'quantity': '1',
                'unit_price': pricelist_item.fixed_price,
                'discount_percent': self.reward_id.discount_percent,
                'price_list_id': self.pricelist_id.id,
                'crm_id': self.booking_id.id,
                'company_id': self.booking_id.company_id.id,
                'source_extend_id': self.booking_id.source_id.id,
                'line_special': True,
                'type': 'service',
                'reward_id': self.reward_id.id,
                'consultants_1': self.env.user.id,
                'note': 'ƯU ĐÃI THẺ THÀNH VIÊN KHÁCH HÀNG %s, HẠNG %s, MÃ THẺ %s' %(self.partner_id.name, self.loyalty_id.rank_id.name, self.loyalty_id.name)
            })
            if self.booking_id.partner_id != self.loyalty_id.partner_id:
                self.env['history.relative.reward'].sudo().create({
                    'booking': self.booking_id.id,
                    'line': line.id,
                    'product': self.product_id.id,
                    'loyalty': self.loyalty_id.id,
                    'customer_name': self.booking_id.partner_id.name,
                    'stage': 'upcoming'
                })
            else:
                self.env['history.used.reward'].sudo().create({
                    'booking_id': self.booking_id.id,
                    'line': line.id,
                    'product': self.product_id.id,
                    'loyalty_id': self.loyalty_id.id,
                    'reward_line_id': self.reward_id.id,
                    'date_used': fields.Datetime.now(),
                    'customer_name': self.partner_id.name,
                    'stage': 'upcoming'
                })
        else:
            pricelist_item = self.env['product.pricelist.item'].sudo().search(
                [('pricelist_id', '=', self.pricelist_id.id),
                 ('product_id', '=', self.product_id.id)], limit=1)
            price_unit = 0
            if pricelist_item:
                if self.product_id.uom_id == self.product_id.uom_so_id:
                    price_unit += pricelist_item.fixed_price
                else:
                    price_unit += self.product_id.uom_id._compute_price(pricelist_item.fixed_price,
                                                                            self.reward_id.product_id.uom_so_id)
            line_product += self.env['crm.line.product'].sudo().create({
                'product_id': self.product_id.id,
                'price_unit': price_unit,
                'product_uom_qty': '1',
                'discount_percent': self.reward_id.discount_percent,
                'product_pricelist_id': self.pricelist_id.id,
                'booking_id': self.booking_id.id,
                'company_id': self.booking_id.company_id.id,
                'source_extend_id': self.booking_id.source_id.id,
                'note': 'ƯU ĐÃI THẺ THÀNH VIÊN KHÁCH HÀNG %s, HẠNG %s, MÃ THẺ %s' %(self.partner_id.name, self.loyalty_id.rank_id.name, self.loyalty_id.name),
                'stage_line_product': 'new',
                'consultants_1': self.env.user.id,
                'reward_id': self.reward_id.id
            })
            if self.booking_id.partner_id != self.loyalty_id.partner_id:
                self.env['history.relative.reward'].sudo().create({
                    'booking': self.booking_id.id,
                    'line_product': line_product.id,
                    'product': self.product_id.id,
                    'loyalty': self.loyalty_id.id,
                    'customer_name': self.booking_id.partner_id.name,
                    'stage': 'upcoming'
                })
            else:
                self.env['history.used.reward'].sudo().create({
                    'booking_id': self.booking_id.id,
                    'line_product': line_product.id,
                    'product': self.product_id.id,
                    'loyalty_id': self.loyalty_id.id,
                    'reward_line_id': self.reward_id.id,
                    'date_used': fields.Datetime.now(),
                    'customer_name': self.partner_id.name,
                    'stage': 'upcoming'
                })
        return self.return_booking_new(self.booking_id)

    def return_booking_new(self, booking):
        return {
            'name': 'Booking guarantee',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.crm_lead_form_booking').id,
            'res_model': 'crm.lead',
            'res_id': booking.id,
        }
