from odoo import fields, models, api
from odoo.exceptions import ValidationError


class CRMLineProductCancel(models.TransientModel):
    _name = 'crm.line.product.cancel'
    _description = 'Wizard hủy line sản phẩm trên Booking'

    crm_line_product_id = fields.Many2one('crm.line.product', string='Sản phẩm')
    name = fields.Char('Lý do hủy')

    def cancel_crm_line_product(self):
        self.crm_line_product_id.write({
            'stage_line_product': 'cancel',
            'note': self.name,
            'product_uom_qty': 0,
            'discount_percent': 0,
            'discount_cash': 0,
            'discount_other': 0
        })
