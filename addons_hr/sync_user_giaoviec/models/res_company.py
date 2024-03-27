import json

import requests

from odoo import fields, api, models
from odoo.addons.queue_job.job import job


class ResCompany(models.Model):
    _inherit = 'res.company'

    @job
    def sync_record(self, id):
        config = self.env['ir.config_parameter'].sudo()
        url_root = config.get_param('url_giaoviec')
        company_id = self.env['res.company'].sudo().browse(id)
        if company_id:
            url = url_root + "/api/v1/sync_res_company"

            payload = json.dumps({
                "erp_id": id,
                "name": company_id.name,
                "code": company_id.code
            })
            headers = {
                'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, data=payload)

    @api.model
    def create(self, vals):
        res = super(ResCompany, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_hr_company').sync_record(id=res.id)
        return res

    def write(self, vals):
        res = super(ResCompany, self).write(vals)
        if res:
            for rc in self:
                if rc.id:
                    rc.sudo().with_delay(priority=0, channel='sync_hr_company').sync_record(id=rc.id)
        return res
