from odoo import fields, api, models


class ListCodeCard(models.Model):
    _name = 'crm.loyalty.code.card'
    _description = 'List Code Card'

    name = fields.Char('Name')
    stage = fields.Selection([('allow', 'allowed to use'), ('using', 'Using')], string='Stage')
    brand_id = fields.Many2one('res.brand', string='Brand')
    loyalty_id = fields.Many2one('crm.loyalty.card', string='Loyalty')


class HistoryRank(models.Model):
    _name = 'crm.loyalty.history.rank'
    _description = 'History Rank'

    name = fields.Char('Name')
    rank_new = fields.Many2one('crm.loyalty.rank', string='Rank new')
    rank_old = fields.Many2one('crm.loyalty.rank', string='Rank old')
    reason = fields.Char('Reason')
