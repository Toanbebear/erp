from odoo import fields, models


class AdviseDesire(models.Model):
    _inherit = 'sale.order'

    sale_order_debt_id = fields.One2many('sale.order.debt', 'sale_order_id', string='Lịch sử trả nợ')