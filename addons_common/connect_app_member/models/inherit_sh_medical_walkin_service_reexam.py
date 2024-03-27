import json
import logging
import requests

from odoo import fields, models, api
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class InheritSHWalkinReexam(models.Model):
    _inherit = 'sh.medical.walkin.service.reexam'

    @job
    def sync_record(self, id, brand_code):
        _logger.info("=====================================sync=========================================")
        params = self.env['ir.config_parameter'].sudo()
        config_sync = 'sync_app_member_%s' % brand_code.lower()
        config_domain = 'config_domain_app_member_%s' % brand_code.lower()
        config_token = 'config_token_app_member_%s' % brand_code.lower()
        domain = params.get_param(config_domain)
        token = params.get_param(config_token)
        sync = params.get_param(config_sync)
        if sync == 'True':
            body = {
                'id': id,
            }
            url = domain + '/api/v1/delete-reexam-line'
            _logger.info(url)
            headers = {
                'Authorization': token,
                'Content-Type': 'application/json'
            }
            response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)

    def unlink(self):
        for rec in self:
            if rec.id:
                brand_code = rec.reexam_id.walkin.institution.his_company.brand_id.code
                rec.sudo().with_delay(priority=0, channel='sync_app_member_reexam_line').sync_record(id=rec.id,
                                                                                                     brand_code=brand_code)
        return super(InheritSHWalkinReexam, self).unlink()
