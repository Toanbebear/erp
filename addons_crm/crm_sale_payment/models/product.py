from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.template'

    commission_percentage = fields.Float(string='Commission percentage')




