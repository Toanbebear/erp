import json
import logging
from datetime import datetime
from odoo.exceptions import ValidationError
import threading
import requests
import time
from odoo import fields, models, api

from odoo.addons.restful.common import (
    get_redis
)

_logger = logging.getLogger(__name__)


class ResCountryState(models.Model):
    _inherit = 'res.country.state'
    _order = "sequence"

    sequence = fields.Integer(default=10)
    cs_id = fields.Integer()

    def write(self, values):
        res = super(ResCountryState, self).write(values)
        if any(key in values for key in ['name', 'country_id', 'code']):
            self.recache(self.country_id.id)
        return res

    @api.model
    def create(self, values):
        res = super(ResCountryState, self).create(values)
        self.recache(res.country_id.id)
        return res

    def unlink(self):
        res = super(ResCountryState, self).unlink()
        self.recache(self.country_id.id)
        return res

    def recache(self, country_id):
        redis_client = get_redis()
        if redis_client:
            redis_client.set(self.get_key(country_id),
                             json.dumps(self.get_data(country_id), indent=4, sort_keys=True, default=str))

    def get_data(self, country_id=None):
        domain = [('country_id', '=', country_id)]
        fields = ['id', 'name', 'code', 'country_id']
        countries = self.env['res.country.state'].search_read(domain, fields)
        for item in countries:
            country_id = item['country_id']
            if isinstance(country_id, tuple):
                item['country_id'] = country_id[0]
                item['country_name'] = country_id[1]
        return countries

    def get_key(self, country_id=None):
        if country_id:
            return "%s_res_country_state" % country_id
        else:
            return "res_country_state"

    def api_get_data(self, country_id, offset=0, limit=None, order=None):
        key = self.get_key()
        if country_id:
            key = self.get_key(country_id)
        if not offset:
            redis_client = get_redis()
            if redis_client:
                data = redis_client.get(key)
                if data:
                    return json.loads(data)

        result = self.get_data()
        if country_id:
            result = self.get_data(country_id)
        if result:
            # Khi không phân trang mới set vào cache, còn phân trang tính sau
            if not offset:
                if redis_client:
                    redis_client.set(key, json.dumps(result, indent=4, sort_keys=True, default=str))
        return result
