from odoo import api, fields, models


class RankReward(models.Model):
    _name = 'crm.loyalty.rank.reward'
    _description = 'Cấu hình Voucher'

    name = fields.Char('Tên voucher', required=True)
    type = fields.Selection([('prd', 'Sản phẩm'), ('service', 'Dịch vụ')], string='Loại voucher', required=True,
                            default='prd')
    method = fields.Selection([('gift', 'Tặng'), ('discount', 'Giảm giá')], string='Hình thức ưu đãi', required=True,
                              default='gift')
    product_ids = fields.Many2many('product.product', string='Sản phẩm', required=True)
    number = fields.Integer('Số lượng', required=True, default=1)
    rank = fields.Many2one('crm.loyalty.rank', 'Hạng thẻ', required=True, readonly=True)
    stage = fields.Selection([('allow', 'Đang sử dụng'), ('not_allow', 'Không được sử dụng')], string='Trạng thái',
                             default='allow', readonly=True)
    percent = fields.Float('Giảm giá phần trăm')
    is_birth_day = fields.Boolean('Voucher dành cho sinh nhật')

    @api.onchange('type')
    def get_domain_field(self):
        if self.type:
            if self.type == 'prd':
                return {'domain': {'product_ids': [('type', '=', 'product')]}}
            elif self.type == 'service':
                return {'domain': {'product_ids': [('type_product_crm', '=', 'service_crm'), ('type', '=', 'service')]}}

    @api.model
    def create(self, vals):
        res = super(RankReward, self).create(vals)
        if res and not res.is_birth_day:
            loyalties = self.env['crm.loyalty.card'].sudo().search([('rank_id', '=', res.rank.id)])
            for loyalty in loyalties:
                self.env['crm.loyalty.line.reward'].sudo().create({
                    'name': res.name,
                    'brand_id': res.rank.brand_id.id,
                    'rank_id': res.rank.id,
                    'type_reward': res.type,
                    'product_ids': res.product_ids.ids,
                    'preferential_method': res.method,
                    'quantity': res.number,
                    'number_use': 0,
                    'discount_percent': res.percent if res.method == 'discount' else 100,
                    'stage': 'allow',
                    'loyalty_id': loyalty.id,
                    'reward_id': res.id
                })
        return res

    def write(self, vals):
        res = super(RankReward, self).write(vals)
        if res:
            reward = self.env['crm.loyalty.line.reward'].sudo().search([('reward_id', '=', self.id)])
            reward.sudo().write({
                'name': self.name,
                'brand_id': self.rank.brand_id.id,
                'rank_id': self.rank.id,
                'type_reward': self.type,
                'product_ids': self.product_ids.ids,
                'preferential_method': self.method,
                'quantity': self.number,
                'discount_percent': self.percent if self.method == 'discount' else 100,
                'reward_id': self.id
            })
        return res

    def button_cancel(self):
        if self.stage == 'allow':
            self.stage = 'not_allow'
            update_line = """
            update crm_loyalty_line_reward set stage = 'not_allow'
            where reward_id = %s and stage = 'allow'
            """
            self._cr.execute(update_line % int(self.id))
