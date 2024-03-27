import json
import logging

from odoo import models, api

from odoo.addons.restful.common import (
    get_redis
)

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def write(self, values):
        res = super(AccountJournal, self).write(values)
        if self.brand_id and any(key in values for key in ['name', 'company_id', 'type']):
            self.recache(res.company_id.id, res.type)
        return res

    @api.model
    def create(self, values):
        res = super(AccountJournal, self).create(values)
        self.recache(self.company_id.id, self.type)
        return res

    def unlink(self):
        brand_id = self.brand_id.id
        res = super(AccountJournal, self).unlink()
        self.recache(self.company_id.id, self.type)
        return res

    def recache(self, company_id, type):
        """
            recache
        """
        redis_client = get_redis()
        if redis_client:
            if not type:
                redis_client.set(self.get_key(company_id),
                                 json.dumps(self.get_data(company_id), indent=4, sort_keys=True, default=str))
            else:
                redis_client.set(self.get_key(company_id, type),
                                 json.dumps(self.get_data(company_id, type), indent=4, sort_keys=True, default=str))

    def get_data(self, company_id, type=None):
        domain = [('company_id', '=', company_id), ('active', '=', True)]
        if type:
            domain += [('type', '=', type)]
        fields = ['id', 'name', 'company_id', 'type']
        return self.env['account.journal'].search_read(domain, fields)

    def get_key(self, company_id, type=None):
        if company_id:
            if type:
                return '%s_%s_account_journal' % (company_id, type)
            else:
                return '%s_account_journal' % company_id
        else:
            return "account_journal"

    def api_get_data(self, company_id, type=None, offset=0, limit=None, order=None):
        key = self.get_key(company_id)
        if type:
            key = self.get_key(company_id, type)

        # Phân trang thì lấy luôn trong db
        if not offset:
            redis_client = get_redis()
            if redis_client:
                data = redis_client.get(key)
                if data:
                    return json.loads(data)

        result = self.get_data(company_id)
        if type:
            result = self.get_data(company_id, type)
        if result:
            # Khi không phân trang mới set vào cache, còn phân trang tính sau
            if not offset:
                if redis_client:
                    redis_client.set(key, json.dumps(result, indent=4, sort_keys=True, default=str))
        return result
