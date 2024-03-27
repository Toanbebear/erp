from odoo.addons.restful.common import (get_redis_server)

import json
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class ResCountry(models.Model):
    _inherit = 'res.country'

    def write(self, values):
        res = super(ResCountry, self).write(values)
        # 'code', 'name', 'phone_code', active
        if any(key in values.keys() for key in ['code', 'name', 'phone_code', 'active', 'sequence']):
            self.recache()
        return res

    @api.model
    def create(self, values):
        res = super(ResCountry, self).create(values)
        self.recache()
        return res

    def unlink(self):
        res = super(ResCountry, self).unlink()
        self.recache()
        return res

    def recache(self):
        # recache: lấy tất cả
        redis_client = get_redis_server()
        if redis_client:
            redis_client.set(self.get_key(),
                             json.dumps(self.get_data(domain=[], offset=0, limit=None, order=None),
                                        indent=4, sort_keys=False, default=str))

    def get_data(self, domain, offset, limit, order):
        fields = ['id', 'code', 'name', 'phone_code']
        return self.env['res.country'].search_read(domain, fields, offset, limit, order)

    def get_key(self):
        return "api_country"

    def api_get_data_country(self, domain=None, offset=0, limit=None, order=None):
        """ Trả về danh sách tất cả các nước trong hệ thống"""
        if domain is None:
            domain = []
        key = self.get_key()
        redis_client = get_redis_server()
        if redis_client:
            data = redis_client.get(key)
            if data:
                _logger.info('REDIS: api_country get from cache')
                return json.loads(data)

        result = self.get_data(domain, offset, limit, order)
        if result:
            # Lưu lại cache
            if redis_client:
                redis_client.set(key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result
