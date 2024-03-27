from odoo import api, models, fields
from odoo.addons.queue_job.job import job
from .. import common
import json
import requests
import logging


_logger = logging.getLogger(__name__)

class CollaboratorsInherit(models.Model):
    _inherit = 'crm.collaborators'

    @job
    def sync_record_channel_job_update_crm_collaborators(self, id):
        ctv = self.sudo().browse(id)
        if ctv.check_ehc:
            url = common.get_url() + "/api/v1/create-collaborators"
            token = common.get_token()
            headers = {
                'authorization': token,
                'Content-Type': 'application/json'
            }
            payload = json.dumps({
                "name": ctv.name,
                "code": ctv.code_collaborators,
                "phone": ctv.phone
            })
            response = requests.request('POST', url=url, data=payload, headers=headers)
        else:
            return False

    @api.model
    def create(self, vals_list):
        res = super(CollaboratorsInherit, self).create(vals_list)
        if res:
            self.sudo().with_delay(priority=0, channel='channel_job_create_crm_collaborators').sync_record_channel_job_update_crm_collaborators(id=res.id)
        return res

    def write(self, vals_list):
        res = super(CollaboratorsInherit, self).write(vals_list)
        if res and vals_list:
            self.sudo().with_delay(priority=0,
                                   channel='channel_job_create_crm_collaborators').sync_record_channel_job_update_crm_collaborators(id=self.id)
        return res
