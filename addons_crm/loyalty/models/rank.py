from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class CrmRank(models.Model):
    _name = 'crm.loyalty.rank'
    _description = 'Crm Rank'

    name = fields.Char('Name')
    rank_low_id = fields.Many2one('crm.loyalty.rank', string='Rank low',
                                  domain="[('brand_id','=',brand_id),('money_end','<',money_fst)]")
    brand_id = fields.Many2one('res.brand', string='Brand', default=lambda self: self.env.company.brand_id)
    money_fst = fields.Float('Money first')
    money_end = fields.Float('Money end')
    active = fields.Boolean('Active', default=True)
    reward_ids = fields.One2many('crm.loyalty.line.reward', 'rank_id', string='Reward')
    date_special = fields.Many2many('crm.loyalty.date', string='Special date')
    money_reward = fields.Monetary('Money reward')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    time_active = fields.Integer('Time active')
    validity_card = fields.Integer('Validity card')

    @api.constrains('money_fst', 'money_end')
    def constrain_money(self):
        for rec in self:
            if rec.money_fst > rec.money_end:
                raise ValidationError(_('The first money cannot be greater than the last one'))
            elif rec.money_end == 0:
                raise ValidationError(_('End money cannot be zero'))

    _sql_constraints = [
        ('name_active_rank', 'unique(brand_id,money_fst,money_end)',
         "Điều kiện của hạng thẻ này đã tồn tại"),
    ]
