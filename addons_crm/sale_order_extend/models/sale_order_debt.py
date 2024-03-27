from odoo import fields, models


class SaleOrderDebt(models.Model):
    _name = 'sale.order.debt'
    _description = 'Lịch sử trả nợ'

    sequence = fields.Integer(default=10)
    product_id = fields.Many2one('product.product', string='Sản phẩm')
    uom_price = fields.Float('Đơn vị xử lý')
    product_uom_qty = fields.Float('Số lượng')
    price_subtotal = fields.Monetary('Thành tiền')
    amount_owned = fields.Monetary('Tiền nợ')
    amount_paid = fields.Monetary('Tiền đã trả')
    record_date = fields.Date('Ngày ghi nhận')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.company.currency_id)
    sale_order_id = fields.Many2one('sale.order')
    note = fields.Char('Ghi chú')