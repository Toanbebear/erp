from odoo import fields, models, api


class CostItemConfig(models.Model):
    _name = 'cost.item.config'
    _description = 'Cấu hình nhóm hạng mục chi phí'

    code = fields.Char(string='Mã nhóm hạng mục')
    name = fields.Char(string='Nhóm hạng mục')
    source = fields.Many2one(comodel_name='source.config.account', string='Nguồn/Khối')
    cost = fields.Boolean(string='Tiền quảng cáo')
