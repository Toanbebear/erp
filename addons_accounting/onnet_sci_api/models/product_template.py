
from odoo import models, api, fields, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_default_code(self):
        super(ProductTemplate, self)._compute_default_code()
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in (self - unique_variants):
            if template.default_code == '':
                template.default_code = False