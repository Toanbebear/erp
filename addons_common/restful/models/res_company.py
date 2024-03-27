from odoo.addons.restful.common import (get_redis_server)

import json
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    def write(self, values):
        res = super(ResCompany, self).write(values)
        if self.brand_id and any(key in values.keys() for key in ['code', 'name', 'brand_id']):
            self.recache(self.brand_id.id)
        return res

    @api.model
    def create(self, values):
        res = super(ResCompany, self).create(values)
        self.recache(res.brand_id.id)
        return res

    def unlink(self):
        brand_id = self.brand_id.id
        res = super(ResCompany, self).unlink()
        self.recache(brand_id)
        return res

    def recache(self, brand_id):
        # recache
        redis_client = get_redis_server()
        if redis_client:
            redis_client.set(self.get_key(brand_id),
                             json.dumps(self.get_data(brand_id), indent=4, sort_keys=False, default=str))

    def get_data(self, brand_id):
        domain = [('brand_id', '=', brand_id), ('code', '!=', 'KN.HCM.03')]
        fields = ['id', 'code', 'name']
        return self.env['res.company'].search_read(domain, fields)

    def get_key_company(self, brand_id):
        if brand_id:
            return 'api_%s_company' % brand_id
        else:
            return "api_all_company"

    def api_get_data_company(self, brand_id=None, offset=0, limit=None, order=None):
        key = self.get_key_company(brand_id)

        # Phân trang thì lấy luôn trong db
        redis_client = get_redis_server()
        if redis_client:
            data = redis_client.get(key)
            if data:
                _logger.info('REDIS: %s get from cache' % key)
                return json.loads(data)

        result = self.get_data(brand_id)
        if result:
            if redis_client:
                redis_client.set(key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result
