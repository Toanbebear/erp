import json
import logging
from datetime import datetime, timedelta
import requests

from odoo import fields, models, api
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class InheritShMedicalCenterService(models.Model):
    _inherit = 'sh.medical.health.center.service'

    sync_name = fields.Char(_compute="get_sync_name", store=True)

    @api.constrains('name')
    def get_sync_name(self):
        name = self.name
        self.sync_name = name
        print(self.sync_name)

    @job
    def sync_record(self, id):
        brand = ''
        service = self.sudo().browse(id)
        default_code = service.default_code
        if default_code:
            if default_code[0] == "P":
                brand = 'pr'
            if default_code[0] == "K" and default_code[1] == "N":
                brand = 'kn'
        if brand != '':
            params = self.env['ir.config_parameter'].sudo()
            config_domain = 'config_domain_app_member_%s' % brand
            config_token = 'config_token_app_member_%s' % brand
            domain = params.get_param(config_domain)
            token = params.get_param(config_token)
            config_sync = 'sync_app_member_%s' % brand.lower()
            sync = self.env['ir.config_parameter'].sudo().get_param(config_sync)
            if sync == 'True':
                if domain and token:
                    body = {
                        'name': service.sync_name,
                        'erp_id': service.id,
                        'default_code': service.code,
                        'id_service_group': service.service_category.id,
                        'product_id': service.product_id.id
                    }
                    url = domain + '/api/v1/sync-service'
                    headers = {
                        'Authorization': token,
                        'Content-Type': 'application/json'
                    }
                    response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)

    def write(self, vals):
        res = super(InheritShMedicalCenterService, self).write(vals)
        if res:
            for service in self:
                if service.id:
                    service.sudo().with_delay(priority=0, channel='sync_app_member_service').sync_record(id=service.id)
        return res

    @api.model
    def create(self, vals):
        res = super(InheritShMedicalCenterService, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_app_member_service').sync_record(id=res.id)
        return res
