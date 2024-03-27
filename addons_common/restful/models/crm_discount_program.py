import json
import logging

from odoo import models, api

from odoo.addons.restful.common import (
    get_redis
)

_logger = logging.getLogger(__name__)


class CRMDiscountProgram(models.Model):
    _inherit = 'crm.discount.program'

    def write(self, values):
        res = super(CRMDiscountProgram, self).write(values)
        if self.brand_id and any(key in values for key in ['name', 'code', 'brand_id', 'company_ids', 'campaign_id', 'stage_prg']):
            self.recache(self.brand_id.id)
        return res

    @api.model
    def create(self, values):
        res = super(CRMDiscountProgram, self).create(values)
        self.recache(res.brand_id.id)
        return res

    def unlink(self):
        brand_id = self.brand_id.id
        res = super(CRMDiscountProgram, self).unlink()
        self.recache(brand_id)
        return res

    def recache(self, brand_id):
        """
            recache
        """
        redis_client = get_redis()
        if redis_client:
            redis_client.set(self.get_key(brand_id),
                             json.dumps(self.get_data(brand_id), indent=4, sort_keys=True, default=str))

    def get_data(self, brand_id, id=None):
        domain = [('active', '=', True), ('brand_id', '=', brand_id), ('stage_prg', '=', 'active')]
        if id:
            domain += [('id', '=', id)]
        fields = ['id', 'code', 'name', 'brand_id', 'campaign_id', 'stage_prg', 'company_ids']
        return self.env['crm.discount.program'].search_read(domain, fields)

    def get_key(self, brand_id, id=None):
        if brand_id:
            if id:
                return '%s_%s_discount_program' % (brand_id, id)
            else:
                return '%s_discount_program' % brand_id
        else:
            return "discount_program"

    def api_get_data(self, brand_id=None, id=None, offset=0, limit=None, order=None):
        key = self.get_key(brand_id)
        if id:
            key = self.get_key(brand_id, id)
        # Phân trang thì lấy luôn trong db
        if not offset:
            redis_client = get_redis()
            if redis_client:
                data = redis_client.get(key)
                if data:
                    return json.loads(data)

        result = self.get_data(brand_id)
        if id:
            result = self.get_data(brand_id, id)
        if result:
            # Khi không phân trang mới set vào cache, còn phân trang tính sau
            if not offset:
                if redis_client:
                    redis_client.set(key, json.dumps(result, indent=4, sort_keys=True, default=str))
        return result