from odoo.addons.restful.common import (
    get_redis
)

import json
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    def write(self, values):
        res = super(ProductCategory, self).write(values)
        if any(key in values.keys() for key in ['name', 'code']):
            self.recache()
        return res
    @api.model
    def create(self, values):
        res = super(ProductCategory, self).create(values)
        self.recache()
        return res

    def unlink(self):
        brand_id = self.brand_id.id
        res = super(ProductCategory, self).unlink()
        self.recache()
        return res

    def recache(self):
        # recache
        redis_client = get_redis()
        if redis_client:
            redis_client.set(self.get_key(),
                             json.dumps(self.get_data(), indent=4, sort_keys=True, default=str))

    def get_data(self):
        domain = []
        fields = ['id', 'code', 'name']
        return self.env['product.category'].search_read(domain, fields)

    def get_key(self):
        return "product_category"

    def api_get_data(self, offset=0, limit=None, order=None):
        key = self.get_key()
        # Phân trang thì lấy luôn trong db
        if not offset:
            redis_client = get_redis()
            if redis_client:
                data = redis_client.get(key)
                if data:
                    return json.loads(data)

        result = self.get_data()
        if result:
            # Khi không phân trang mới set vào cache, còn phân trang tính sau
            if not offset:
                if redis_client:
                    redis_client.set(key, json.dumps(result, indent=4, sort_keys=True, default=str))
        return result
