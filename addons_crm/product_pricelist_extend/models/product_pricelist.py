from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    is_price_min_max = fields.Boolean('Bảng giá trong khoảng', default=False)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    price_min = fields.Monetary('Giá min')
    is_price_min_max = fields.Boolean('Bảng giá trong khoảng')
