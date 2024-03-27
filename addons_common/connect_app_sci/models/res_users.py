import json
import logging

import requests

from odoo import models, fields, api
from odoo.http import request
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class ResUsersInherit(models.Model):
    _inherit = "res.users"

    @job
    def sync_user_app_sci(self, id):
        domain = self.env['ir.config_parameter'].sudo().get_param('domain_app_sci')
        token = self.env['ir.config_parameter'].sudo().get_param('token_app_sci')
        user = self.sudo().browse(id)
        body = {
            'id_erp': user.id,
            'login': user.login,
            'name': user.name,
        }
        url = domain + '/api/sync-user'
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }
        response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)

    @api.model
    def create(self, vals):
        res = super(ResUsersInherit, self).create(vals)
        if res.id:
            res.sudo().with_delay(priority=0, channel='sync_user_erp_app_sci').sync_user_app_sci(id=res.id)
        return res

    def write(self, vals):
        res = super(ResUsersInherit, self).write(vals)
        if res:
            for rec in self:
                if rec.id:
                    rec.sudo().with_delay(priority=0, channel='sync_user_erp_app_sci').sync_user_app_sci(id=rec.id)
        return res
