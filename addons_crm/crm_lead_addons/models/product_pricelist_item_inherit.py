from odoo import fields, models, api
from odoo.osv import expression

NEGATIVE_TERM_OPERATORS = ('!=', 'not like', 'not ilike', 'not in')


class ProductPriceListItemInherit(models.Model):
    _inherit = 'sh.medical.health.center.service'

    def name_get(self):
        result = super(ProductPriceListItemInherit, self).name_get()
        if self._context.get('name_service_with_price'):
            new_result = []
            for sub_res in result:
                rec = self.env['sh.medical.health.center.service'].browse(sub_res[0])
                price_list_id = self.env['product.pricelist'].browse(self._context.get('pricelist'))
                price_id = price_list_id.item_ids.filtered(lambda x: x.product_id.id == rec.product_id.id)
                # name = sub_res[1] + str("{:,}".format(int(price_id.fixed_price)))
                name = sub_res[1] + ' -  %s đ' % "{:,}".format(int(price_id.fixed_price))
                new_result.append((sub_res[0], name))
            return new_result
        return result

    # def name_get(self):
    #
    #     if self._context.get('name_service_with_price'):
    #         result = []
    #         for rec in self:
    #             price_list_id = self.env['product.pricelist'].browse(self._context.get('pricelist'))
    #             price_id = price_list_id.item_ids.filtered(lambda x: x.product_id.id == rec.product_id.id)
    #             name = ' - '.join((rec.default_code, rec.name, "{:,}".format(int(price_id.fixed_price)) + 'đ'))
    #             result.append((rec.id, name))
    #         return result
    #     else:
    #         return super(ProductPriceListItemInherit, self).name_get()
