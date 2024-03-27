from odoo import fields, models, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    price_min = fields.Monetary('Giá Min')
    discount_cs_percent = fields.Float('Giảm giá cơ sở %')
    discount_cs_amount = fields.Monetary('Giảm giá cơ sở')
    total_discount_review = fields.Monetary('Giảm giá sâu')

    @api.depends('product_uom_qty', 'discount', 'discount_cash', 'price_unit', 'tax_id', 'uom_price', 'other_discount', 'discount_cs_percent', 'discount_cs_amount')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.sale_to == 0:
                price = line.price_unit * (
                        1 - (line.discount or 0.0) / 100.0) - line.discount_cash - line.other_discount
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                product=line.product_id, partner=line.order_id.partner_shipping_id)
                total = line.price_unit * line.product_uom_qty * line.uom_price * (
                        1 - (line.discount or 0.0) / 100.0) - line.discount_cash - line.other_discount - line.discount_cs_amount - line.total_discount_review
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': total,
                    'price_subtotal': total,
                })
            else:
                total = line.sale_to * line.product_uom_qty
                line.update({
                    'price_total': total,
                    'price_subtotal': total,
                })

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        if res.crm_line_id:
            if res.crm_line_id.discount_cs_amount and res.crm_line_id.discount_cs_percent:
                res.discount_cs_amount = ((res.crm_line_id.discount_cs_amount / (res.crm_line_id.quantity * res.crm_line_id.uom_price)) * res.uom_price)
                res.discount_cs_percent = res.crm_line_id.discount_cs_percent
            res.total_discount_review = res.crm_line_id.total_discount_review
        return res
