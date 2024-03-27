import json
import logging

from odoo import models, api

from odoo.addons.restful.common import (
    get_redis, get_redis_server
)

_logger = logging.getLogger(__name__)


class UtmCampaign(models.Model):
    _inherit = 'utm.campaign'

    def write(self, values):
        res = super(UtmCampaign, self).write(values)
        if self.brand_id and any(key in values.keys() for key in ['name', 'active', 'brand_id', 'campaign_status']):
            self.recache(self.brand_id.id)
        return res

    @api.model
    def create(self, values):
        res = super(UtmCampaign, self).create(values)
        self.recache(res.brand_id.id)
        return res

    def unlink(self):
        brand_id = self.brand_id.id
        res = super(UtmCampaign, self).unlink()
        self.recache(brand_id)
        return res

    def recache(self, brand_id):
        """
            recache
        """
        redis_client = get_redis_server()
        if redis_client:
            redis_client.set(self.get_key(brand_id),
                             json.dumps(self.get_data(brand_id), indent=4, sort_keys=False, default=str))

    def get_data(self, brand_id, id=None):
        """
           3 là trạng thái kết thúc
        """
        domain = [('campaign_status', '!=', 3), ('brand_id', '=', brand_id)]
        if id:
            domain += [('id', '=', id)]
        fields = ['id', 'name', 'brand_id']
        return self.env['utm.campaign'].search_read(domain, fields)

    def get_key(self, brand_id, id=None):
        if brand_id:
            if id:
                return '%s_%s_utm_campaign' % (brand_id, id)
            else:
                return '%s_utm_campaign' % brand_id
        else:
            return "utm_campaign"

    def api_get_data_campaign(self, brand_id=None, id=None, offset=0, limit=None, order=None):
        key = self.get_key(brand_id)
        if id:
            key = self.get_key(brand_id, id)

        redis_client = get_redis_server()
        if redis_client:
            data = redis_client.get(key)
            if data:
                _logger.info('REDIS: %s get from cache' % key)
                return json.loads(data)

        result = self.get_data(brand_id)
        if result and redis_client:
            redis_client.set(key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result