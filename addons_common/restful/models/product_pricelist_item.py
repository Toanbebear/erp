import json
import logging
from odoo import models, api, tools

from odoo.addons.restful.common import (
    get_redis
)

_logger = logging.getLogger(__name__)


class ProductProductItem(models.Model):
    _inherit = 'product.pricelist.item'

    def write(self, values):
        # Xử lý khi thay đổi item trong bảng giá
        res = super(ProductProductItem, self).write(values)
        self.product_id.recache(self.pricelist_id.id, self.product_id.default_code)
        return res

    @api.model
    def create(self, values):
        res = super(ProductProductItem, self).create(values)
        res.product_id.recache(res.pricelist_id.id, res.product_id.default_code)
        return res

    def unlink(self):
        res = super(ProductProductItem, self).unlink()
        self.cron_job_sync_redis()
        return res

    def cron_job_sync_redis(self):
        redis_client = get_redis()
        if redis_client:
            pricelist_ids = self.env['product.pricelist'].sudo().search([('active', '=', True)], order='id asc')
            if pricelist_ids:
                pricelist_items = self.env['product.pricelist.item'].sudo().search([('pricelist_id', 'in', pricelist_ids.ids)])
                if pricelist_items:
                    for record in pricelist_items:
                        record.product_id.recache(record.pricelist_id.id, record.product_id.default_code)

    # def recache(self):
    #     # recache
    #     redis_client = get_redis()
    #     if redis_client:
    #         redis_client.set(self.get_key(),
    #                          json.dumps(self.get_data_by_code(), indent=4, sort_keys=True, default=str))
    #
    # def get_key(self, company_id, pricelist_id, code):
    #     return "%s_%s_%s" % (company_id, pricelist_id, code)
    #
    # def get_data_by_code(self,  company_id=None, pricelist_id=None, code=None):
    #     val = None
    #     domain = [('active', '=', True)]
    #     # Lấy dịch vụ theo code
    #     products = self.env['product.product'].search_read([('default_code', '=', code)], ['id'])
    #     product_ids = list([product['id'] for product in products])
    #     if product_ids:
    #         domain.append(('product_id', 'in', product_ids))
    #
    #         company_name = False
    #         if company_id:
    #             company_id = eval(company_id)
    #             company = self.env['res.company'].browse(company_id)
    #             company_name = company.name
    #
    #         # Bảng giá là bắt buộc
    #         if pricelist_id:
    #             product_pricelist = self.env['product.pricelist'].browse(eval(pricelist_id))
    #
    #             if product_pricelist:
    #
    #                 if not company_id:
    #                     company = product_pricelist.company_id
    #                     company_name = company.name
    #                     company_id = company.id
    #
    #         if company_id:
    #             domain.append(('company_id', 'in', [False, company_id]))
    #
    #         domain.append(('pricelist_id', '=', eval(pricelist_id)))
    #
    #         price_list_item = self.env['product.pricelist.item'].search(domain)
    #
    #         product_info = self.env['product.product']
    #         ls_product = []
    #
    #         for rec in price_list_item:
    #             if rec.applied_on == '0_product_variant':  # Biến thể sản phẩm
    #                 ls_product.append(rec)
    #             elif rec.applied_on == '1_product':  # Sản phẩm
    #                 for prd in rec.product_tmpl_id.product_variant_ids:
    #                     ls_product.append(prd)
    #             elif rec.applied_on == '2_product_category':  # Nhóm sản phẩm/dịch vụ
    #                 for prd in product_info.search([('categ_id', '=', rec.categ_id.id)]):
    #                     ls_product.append(prd)
    #             else:  # Tất cả sản phẩm/dịch vụ
    #                 for rec in product_info.search([]):
    #                     ls_product.append(rec)
    #
    #         for record in ls_product:
    #             product = record.product_id
    #             price = tools.format_amount(self.env, record.fixed_price, self.env.ref('base.VND'), 'vn'),
    #             val = {
    #                 'id': product.id,
    #                 'default_code': product.default_code,
    #                 'name': '[%s] %s - %s' % (product.default_code, product.name, price[0]),
    #                 'type': product.type,
    #                 'company': [{'id': company_id, 'name': company_name}],
    #             }
    #             break
    #     return val
