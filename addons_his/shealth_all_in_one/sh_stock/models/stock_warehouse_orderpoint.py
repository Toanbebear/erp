from odoo import fields, models


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    code_product = fields.Char('Mã sản phẩm', related='product_id.default_code')
