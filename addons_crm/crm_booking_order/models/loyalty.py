from odoo import models, fields, api


class LoyaltyLineProductReward(models.Model):
    _inherit = 'crm.loyalty.line.reward'

    crm_line_product_ids = fields.One2many('crm.line.product', 'reward_id', string='Line product')

    @api.depends('loyalty_id', 'number_use', 'quantity', 'type_reward', 'crm_line_ids.stage',
                 'crm_line_product_ids.stage_line_product')
    def check_stage(self):
        for rec in self:
            rec.stage = 'not_allow'
            if rec.type_reward == 'prd':
                if any('new' == stage or 'processing' == stage or 'waiting' == stage for stage in self.crm_line_product_ids.mapped('stage_line_product')):
                    rec.stage = 'processing'
                elif rec.number_use >= rec.quantity:
                    rec.stage = 'used'
                elif rec.reward_parent in rec.loyalty_id.rank_id.reward_ids:
                    rec.stage = 'allow'
                else:
                    rec.stage = 'not_allow'
            elif rec.type_reward == 'service':
                if any('new' == stage or 'processing' == stage or 'waiting' == stage for stage in self.crm_line_ids.mapped('stage')):
                    rec.stage = 'processing'
                elif rec.number_use >= rec.quantity:
                    rec.stage = 'used'
                elif rec.reward_parent in rec.loyalty_id.rank_id.reward_ids:
                    rec.stage = 'allow'
                else:
                    rec.stage = 'not_allow'
            elif rec.type_reward == 'ctg' and rec.loyalty_id:
                if rec.reward_parent in rec.loyalty_id.rank_id.reward_ids:
                    rec.stage = 'allow'
                else:
                    rec.stage = 'not_allow'

    @api.depends('crm_line_ids', 'crm_line_product_ids', 'crm_line_product_ids.stage_line_product')
    def set_number_use(self):
        for rec in self:
            rec.number_use = 0
            if rec.crm_line_ids:
                for i in rec.crm_line_ids:
                    rec.number_use += i.number_used
            elif rec.crm_line_product_ids:
                for i in rec.crm_line_product_ids:
                    if i.stage_line_product == 'sold':
                        rec.number_use += i.product_uom_qty
