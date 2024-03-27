from odoo import fields, models, api, _
from odoo.tools import pycompat
import random


class Wallet(models.Model):
    _name = 'partner.wallet'
    _description = 'Partner wallet'
    _sql_constraints = [
        ('name_name_wallet', 'unique(name)', "Mã ví đã tồn tại"),
    ]

    name = fields.Char('ID')
    partner_id = fields.Many2one('res.partner', string='Customer')
    company_id = fields.Many2one('res.company', string='Company')
    amount_used = fields.Monetary('Amount used', compute='set_amount_used')
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')

    @api.depends('partner_id')
    def set_amount_used(self):
        for rec in self:
            rec.amount_used = 0
            if rec.partner_id:
                orders = self.env['sale.order'].search(
                    [('partner_id', '=', rec.partner_id.id), ('state', 'in', ['sale', 'done']),
                     ('company_id', '=', rec.company_id.id)])
                rec.amount_used = sum(orders.mapped('amount_total'))

    @api.model
    def create(self, vals):
        res = super(Wallet, self).create(vals)
        res.name = self.env['ir.sequence'].next_by_code('partner.wallet')
        return res
