import json
import logging

from odoo import models, api

from odoo.addons.restful.common import (
    get_redis, get_redis_server
)

_logger = logging.getLogger(__name__)


class CrmCategorySource(models.Model):
    _inherit = 'crm.category.source'

    def write(self, values):
        res = super(CrmCategorySource, self).write(values)
        # recache
        self.recache()
        return res

    @api.model
    def create(self, values):
        res = super(CrmCategorySource, self).create(values)
        # recache
        self.recache()
        return res

    def unlink(self):
        res = super(CrmCategorySource, self).unlink()
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

    def get_key(self):
        return "source_category"

    def get_data(self, domain=None, offset=0, limit=None, order=None):
        fields = ['id', 'name']
        return self.env['crm.category.source'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )

    def api_get_source_category(self, domain=[], fields=[], offset=0, limit=None, order=None):
        key = self.get_key()
        redis_client = get_redis_server()
        if redis_client:
            data = redis_client.get(key)
            if data:
                _logger.info('REDIS: %s get from cache' % key)
                return json.loads(data)

        result = self.get_data(domain, offset, limit, order)

        if result and redis_client:
            redis_client.set(key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result
