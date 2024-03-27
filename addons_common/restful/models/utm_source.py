from odoo.addons.restful.common import (
    get_redis_server
)

import json
import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class UtmSource(models.Model):
    _inherit = 'utm.source'

    # Refactor: Sử dụng 2 trường res_id và brand_code hoặc brand_name
    id_kn = fields.Integer('ID KN CS')
    id_da = fields.Integer('ID DA CS')
    id_hh = fields.Integer('ID HH CS')
    id_pr = fields.Integer('ID PR CS')
    id_hv = fields.Integer('ID Academy CS')
    id_rh = fields.Integer('ID Richard CS')

    def write(self, values):
        res = super(UtmSource, self).write(values)
        if any(key in values for key in ['name', 'category_id', 'code', 'active']):
            self.recache()
        return res

    @api.model
    def create(self, values):
        res = super(UtmSource, self).create(values)
        self.recache()
        return res

    def unlink(self):
        res = super(UtmSource, self).unlink()
        self.recache()
        return res

    def recache(self):
        """
            recache
        """
        redis_client = get_redis_server()
        if redis_client:
            redis_client.set(self.get_key(),
                             json.dumps(self.get_data(), indent=4, sort_keys=False, default=str))

    def get_data(self, brand_code=None):
        domain = [('active', '=', True), ('brand_id.code', '=', brand_code)]
        fields = ['id', 'name', 'code', 'category_id']
        sources = self.env['utm.source'].search_read(domain, fields)
        for item in sources:
            category_id = item['category_id']
            if isinstance(category_id, tuple):
                item['category_id'] = category_id[0]
                item['category_name'] = category_id[1]
        return sources

    def get_key(self, brand_code=None):
        return "utm_%s_source" % brand_code

    def api_get_source(self, offset=0, limit=None, order=None, brand_code=None):
        key = self.get_key(brand_code=brand_code)
        # Phân trang thì lấy luôn trong db
        redis_client = get_redis_server()
        if redis_client:
            data = redis_client.get(key)
            if data:
                _logger.info('REDIS: %s get from cache' % key)
                # return json.loads(data)

        result = self.get_data(brand_code=brand_code)
        if result and redis_client:
            redis_client.set(key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result
