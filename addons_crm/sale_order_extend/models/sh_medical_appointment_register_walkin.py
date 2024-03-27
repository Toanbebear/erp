from odoo import fields, models
from datetime import date,datetime

class InheritSHWalkin(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    def set_to_completed(self):
        res = super(InheritSHWalkin, self).set_to_completed()
        if self.sale_order_id.amount_owed > 0:
            for order_line in self.sale_order_id.order_line:
                if order_line.amount_owed > 0:
                    self.env['sale.order.debt'].sudo().create({
                        'product_id': order_line.product_id.id,
                        'uom_price': order_line.uom_price,
                        'product_uom_qty': order_line.product_uom_qty,
                        'price_subtotal': order_line.price_subtotal,
                        'amount_owned': order_line.amount_owed,
                        'amount_paid': 0,
                        'record_date': date.today(),
                        'sale_order_id': self.sale_order_id.id
                    })
    def set_to_progress_admin(self):
        res = super(InheritSHWalkin, self).set_to_progress_admin()
        if self.sale_order_id.amount_owed > 0:
            for order_line in self.sale_order_id.order_line:
                if order_line.amount_owed > 0:
                    self.env['sale.order.debt'].sudo().create({
                        'product_id': order_line.product_id.id,
                        'uom_price': order_line.uom_price,
                        'product_uom_qty': order_line.product_uom_qty,
                        'price_subtotal': order_line.price_subtotal,
                        'amount_owned': 0 - order_line.amount_owed,
                        'amount_paid': 0,
                        'record_date': date.today(),
                        'sale_order_id': self.sale_order_id.id
                    })
