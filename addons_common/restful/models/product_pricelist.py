from odoo.addons.restful.common import (
    get_redis_server
)

import json
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def write(self, values):
        res = super(ProductPricelist, self).write(values)
        if self.brand_id and self.type == 'service' and any(item in values for item in ['active', 'name', 'type', 'currency_id', 'brand_id', 'company_id']):
            self.recache(self.brand_id.id)
        return res

    @api.model
    def create(self, values):
        res = super(ProductPricelist, self).create(values)
        self.recache(res.brand_id.id)
        return res

    def unlink(self):
        brand_id = self.brand_id.id
        res = super(ProductPricelist, self).unlink()
        self.recache(brand_id)
        return res

    def recache(self, brand_id):
        # recache
        redis_client = get_redis_server()
        if redis_client:
            redis_client.set(self.get_key(brand_id),
                             json.dumps(self.get_data(brand_id), indent=4, sort_keys=True, default=str))

    def get_data(self, brand_id, id=None):
        domain = [('active', '=', 'true'), ('type', '=', 'service'), ('brand_id', '=', brand_id)]
        if id:
            domain.append(('id', '=', id))

        records = self.env['product.pricelist'].search(domain)
        data = []
        for record in records:
            brand = record.brand_id
            company = record.company_id
            val = {
                'id': record.id,
                'name': record.name,
                'type': record.type,
                'currency_id': record.currency_id.name,
                'brand': [{'id': brand.id, 'name': brand.name}],
                'company': [{'id': company.id, 'name': company.name}],
            }
            data.append(val)
        return data

    def get_key(self, brand_id, id=None):
        if brand_id:
            if id:
                # Chi tiết 1 bảng giá
                return '%s_price_list_%s' % (brand_id, id)
            else:
                return '%s_price_list' % brand_id
        else:
            # Tất cả thương hiệu
            return "price_list"

    def api_get_all_data_product_price_list(self, brand_id=None, id=None, domain=None, offset=0, limit=None, order=None):
        key = self.get_key(brand_id, id)
        # Kiểm tra redis
        rd = get_redis_server()
        if rd:
            data = rd.get(key)
            if data:
                _logger.info('REDIS: %s get from cache' % key)
                return json.loads(data)

        # Nếu chưa có data thì lấy trong database
        result = self.get_data(brand_id, id)
        if result:
            # Set lại cache
            if rd:
                rd.set(key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result
