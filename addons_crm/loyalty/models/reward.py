from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class LoyaltyLineReward(models.Model):
    _name = 'crm.loyalty.line.reward'
    _description = 'Loyalty Line Reward'

    name = fields.Char('Tên')
    brand_id = fields.Many2one('res.brand', string='Thương hiệu')
    rank_id = fields.Many2one('crm.loyalty.rank', string='Hạng thẻ', domain="[('brand_id','=',brand_id)]")
    loyalty_id = fields.Many2one('crm.loyalty.card', string='Loyalty')
    # reward
    # loai 1 : loại sản phẩm là cho phép khách hàng đc sử dụng miễn phí với số lượng giới hạn
    # loại 2 : loại nhóm sản phẩm cho phép nếu như người dụng chọn sản phẩm trong nhóm này thì sẽ ddc giảm thêm
    # loại 3 : loại ngày đặc biệt cho phép nếu như đến ngày này kh sẽ đc phần quà , và phần quà này có giới hạn time

    type_reward = fields.Selection([('prd', 'Product'), ('ctg', 'Category product'), ('service', 'Dịch vụ')],
                                   string='Ưu đãi theo', default='service')
    quantity = fields.Integer('Số lượng miễn phí', default=1)
    product_ids = fields.Many2many('product.product', string='Sản phẩm/Dịch vụ', domain="[('type','in',['service', 'product'])]")
    number_use = fields.Integer('Số ượng đã sử dụng')
    category_id = fields.Many2many('product.category', string='Nhóm dịch vụ')
    preferential_method = fields.Selection([('gift', 'Tặng'), ('discount', 'Giảm giá')],
                                           string='HÌnh thức ưu đãi', default='gift')
    discount_percent = fields.Float('Mức chiết khấu')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    stage = fields.Selection([('allow', 'Được sử dụng'), ('used', 'Sử dụng hết'), ('processing', 'Đang xử lý'),
                              ('not_allow', 'Không được phép sử dụng')], string='Trạng thái')
    active = fields.Boolean('Active', default=True)
    reward_parent = fields.Many2one('crm.loyalty.line.reward', string='Reward parent')
    crm_line_ids = fields.One2many('crm.line', 'reward_id', string='Line service')
    rank = fields.Char('Document rank')
    end_date = fields.Date('Ngày hết hạn')
    date_use = fields.Date('Ngày sử dụng')

    def write(self, vals):
        res = super(LoyaltyLineReward, self).write(vals)
        if vals.get('number_use'):
            for rec in self:
                if rec.number_use == rec.quantity:
                    rec.write({'stage': 'used'})
        return res

    @api.onchange('type_reward')
    def get_product_by_type_reward(self):
        domain = [('pricelist_id.brand_id', '=', self.brand_id.id)]
        if self.type_reward and self.type_reward == 'prd':
            domain += [('product_id.type', '=', 'product')]
        elif self.type_reward and self.type_reward == 'service':
            domain += [('product_id.type', '=', 'service')]
        product_ids = self.env['product.pricelist.item'].search(domain).mapped('product_id').ids
        return {'domain': {'product_id': [('id', 'in', product_ids)]}}

    # @api.depends('loyalty_id', 'number_use', 'quantity', 'type_reward')
    # def check_stage(self):
    #     # for rec in self:
    #     #     rec.stage = 'not_allow'
    #     #     if rec.type_reward == 'prd' and rec.crm_line_product_ids:
    #     #         if rec.number_use == rec.quantity:
    #     #             rec.stage = 'used'
    #     #         elif rec.voucher_loyalty_id in rec.loyalty_id.rank_id.reward_ids:
    #     #             rec.stage = 'allow'
    #     #         else:
    #     #             rec.stage = 'not_allow'
    #     #     elif rec.type_reward != 'prd' and rec.loyalty_id:
    #     #         if rec.reward_parent in rec.loyalty_id.rank_id.reward_ids:
    #     #             rec.stage = 'allow'
    #     #         else:
    #     #             rec.stage = 'not_allow'
    #     for rec in self:
    #         rec.stage = 'allow'
    #         # if rec.type_reward == 'prd':
    #         #     if rec.number_use == rec.quantity:
    #         #         rec.stage = 'used'
    #         #     elif rec.voucher_loyalty_id in rec.loyalty_id.rank_id.voucher_loyalty_ids:
    #         #         rec.stage = 'allow'
    #         #     else:
    #         #         rec.stage = 'not_allow'
    #         # elif rec.type_reward == 'ctg':
    #         #     pass
    #         # else:
    #         #     pass

    def use_reward(self):
        return {
            'name': 'Sử dụng quà tặng',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('loyalty.use_reward_form').id,
            'res_model': 'crm.loyalty.use.reward',
            'context': {
                'default_reward_id': self.id,
                'default_loyalty_id': self.loyalty_id.id,
                'default_partner_id': self.loyalty_id.partner_id.id,
                'default_type': self.type_reward,
                'default_brand_id': self.loyalty_id.brand_id.id,
            },
            'target': 'new',
        }

    @api.constrains('quantity')
    def check_quantity(self):
        for rec in self:
            if rec.quantity < 1:
                raise ValidationError('Số lượng miễn phí phải lơn hơn hoặc bằng 1')

    @api.constrains('reward')
    def check_reward(self):
        for rec in self:
            if rec.type_reward == 'date_spc' and rec.reward <= 0:
                raise ValidationError('Tiền thưởng không thể nhỏ hơn hoặc bằng 0')

    @api.onchange('type_discount')
    def reset_by_type(self):
        if self.type_reward != 'prd':
            self.quantity = 1
            self.product_id = False
        if self.type_reward != 'ctg':
            self.category_id = False
            self.reward = 0
        if self.type_reward != 'date_spc':
            self.type_date = False
            self.day = 0
            self.reward = 0


class DateSpecial(models.Model):
    _name = 'crm.loyalty.reward.date.special'
    _description = 'Date Special'

    name = fields.Char('Name')
    brand_id = fields.Many2one('res.brand', string='Brand')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    reward_origin = fields.Monetary('Bonus origin')
    reward_used = fields.Monetary('Bonus used')
    reward_remain = fields.Monetary('Bonus remain', compute='set_remain', store=True)
    stage = fields.Selection([('use', 'Allow to use'), ('used_up', 'Used up'), ('expired', 'Expired')], string='Stage')
    loyalty_id = fields.Many2one('crm.loyalty.card', string='Loyalty')
    type = fields.Selection([('reward', 'Reward'), ('use', 'Use')], string='Type')
    active_date = fields.Datetime('Active date')
    end_date = fields.Datetime('End date')
    date_special = fields.Many2one('crm.loyalty.date', string='Date special')
    bonus_date_parent_id = fields.Many2one('crm.loyalty.reward.date.special', string='Bonus date parent')
    bonus_date_child_ids = fields.One2many('crm.loyalty.reward.date.special', 'bonus_date_parent_id',
                                           string='Bonus date child')

    @api.depends('reward_origin', 'reward_used')
    def set_remain(self):
        for rec in self:
            self.reward_remain = self.reward_origin - self.reward_used


class LoyaltyDate(models.Model):
    _name = 'crm.loyalty.date'
    _description = 'Loyalty Date'

    name = fields.Char('Name')
    type = fields.Selection([('b_date', 'Birth date'), ('other', 'Other')], string='Type date')
    brand_id = fields.Many2one('res.brand', string='Brand')
    date = fields.Integer('Date')
    month = fields.Integer('Month')
    reward_ids = fields.Many2many('crm.loyalty.line.reward', 'reward_date_ref', 'reward', 'date', string='Rewards')
    loyalty_ids = fields.Many2many('crm.loyalty.card', 'loyalty_date_ref', 'date_spc', 'loyalty', string='Loyalty')
