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


class ResCountryDistrict(models.Model):
    _inherit = 'res.country.district'
    _order = "sequence"

    sequence = fields.Integer(default=10)
    cs_id = fields.Integer()
    code = fields.Char('Mã')

    def write(self, values):
        res = super(ResCountryDistrict, self).write(values)
        if any(key in values for key in ['name', 'state_id', 'code']):
            self.recache(self.state_id.id)
        return res

    @api.model
    def create(self, values):
        res = super(ResCountryDistrict, self).create(values)
        self.recache(res.state_id.id)
        return res

    def unlink(self):
        res = super(ResCountryDistrict, self).unlink()
        self.recache(self.state_id.id)
        return res

    def recache(self, state_id):
        redis_client = get_redis()
        if redis_client:
            redis_client.set(self.get_key(state_id),
                             json.dumps(self.get_data(state_id), indent=4, sort_keys=True, default=str))

    def get_data(self, state_id=None):
        domain = [('state_id', '=', state_id)]
        fields = ['id', 'name', 'code', 'state_id']
        districts = self.env['res.country.district'].sudo().search_read(domain, fields)
        for item in districts:
            state_id = item['state_id']
            if isinstance(state_id, tuple):
                item['state_id'] = state_id[0]
                item['state_name'] = state_id[1]
        return districts

    def get_key(self, state_id=None):
        if state_id:
            return "%s_res_country_district" % state_id
        else:
            return "res_country_district"

    def api_get_data(self, state_id, offset=0, limit=None, order=None):
        key = self.get_key()
        if state_id:
            key = self.get_key(state_id)
        if not offset:
            redis_client = get_redis()
            if redis_client:
                data = redis_client.get(key)
                if data:
                    return json.loads(data)

        result = self.get_data()
        if state_id:
            result = self.get_data(state_id)
        if result:
            # Khi không phân trang mới set vào cache, còn phân trang tính sau
            if not offset:
                if redis_client:
                    redis_client.set(key, json.dumps(result, indent=4, sort_keys=True, default=str))
        return result