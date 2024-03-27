from odoo import api, fields, models


class InheritCRMLoyaltyRank(models.Model):
    _inherit = 'crm.loyalty.rank'

    voucher_loyalty_ids = fields.One2many('voucher.loyalty','rank', string='Cấu hình Voucher')



