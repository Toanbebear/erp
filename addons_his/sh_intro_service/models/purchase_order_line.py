from odoo import api, fields, models, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    price_unit_recently = fields.Float(_('Đơn giá gần nhất'), readonly=True, compute="_compute_price_unit_recently")

    @api.depends('product_id')
    def _compute_price_unit_recently(self):
        for rec in self:
            rec.price_unit_recently = 0
            pl = self.env['purchase.order.line'].sudo().search([('product_id', '=', rec.product_id.id), ('order_id.state', 'in', ('purchase', 'done'))], limit=1, order='create_date DESC')
            if pl:
                rec.price_unit_recently = pl.price_unit