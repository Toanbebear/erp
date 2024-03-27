import json
import logging
from datetime import datetime
import requests
from odoo.addons.queue_job.job import job

from odoo import models

_logger = logging.getLogger(__name__)


class InheritReexam(models.Model):
    _inherit = 'sh.medical.reexam'

    @job
    def sync_record(self, id, type):
        reexam = self.sudo().browse(id)
        # account = self.env['account.app.member'].sudo().search([('phone', '=', reexam.walkin.booking_id.phone)])
        # if account:
        brand = reexam.walkin.institution.his_company.brand_id.code
        params = self.env['ir.config_parameter'].sudo()
        config_domain = 'config_domain_app_member_%s' % brand.lower()
        config_token = 'config_token_app_member_%s' % brand.lower()
        config_sync = 'sync_app_member_%s' % brand.lower()
        sync = params.get_param(config_sync)
        domain = params.get_param(config_domain)
        token = params.get_param(config_token)
        if sync == 'True':
            if domain and token:
                if type == 'confirm':
                    reexam_line_ids_data = []
                    for reexam_line in reexam.days_reexam_print:
                        type_reexam = reexam_line.type
                        if type_reexam not in ["Check", "Check1", "Check2", "Check3", "Check4", "Check5", "Check6",
                                               "Check7", "Check8"]:
                            reexam_line_id_data = {
                                'name': reexam_line.name,
                                'type': reexam_line.type,
                                'date_recheck': reexam_line.date_recheck_print.strftime("%m/%d/%Y"),
                                'for_services': reexam_line.for_service,
                                'erp_id': reexam_line.id,
                            }
                            reexam_line_ids_data.append(reexam_line_id_data)
                    body = {
                        'name_reexam': reexam.name,
                        'company_reexam': reexam.company.code,
                        'date_reexam': reexam.date.strftime("%m/%d/%Y"),
                        'date_out_reexam': reexam.date_out.strftime("%m/%d/%Y"),
                        'reexam_ids': reexam_line_ids_data,
                        'info_take_care': reexam.info,
                        'walkin': reexam.walkin.name,
                        'institution': reexam.walkin.institution.his_company.code,
                        'erp_id': reexam.id,
                        'state': reexam.state,
                    }
                    url = domain + '/api/v1/sync-reexam'
                    headers = {
                        'Authorization': token,
                        'Content-Type': 'application/json'
                    }
                    response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)
                else:
                    url = domain + '/api/v1/cancel-reexam'
                    headers = {
                        'Authorization': token,
                        'Content-Type': 'application/json'
                    }
                    body = {
                        'state': reexam.state,
                        'erp_id': reexam.id
                    }
                    response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)

    def action_confirm_reexam(self):
        res = super(InheritReexam, self).action_confirm_reexam()
        if res and self.id:
            self.sudo().with_delay(priority=0, channel='sync_app_member_reexam').sync_record(id=self.id, type='confirm')
        return res

    def set_to_cancelled(self):
        res = super(InheritReexam, self).set_to_cancelled()
        if res and self.id:
            account = self.env['account.app.member'].sudo().search([('phone', '=', self.walkin.booking_id.phone)])
            if account:
                self.sudo().with_delay(priority=0, channel='sync_app_member_reexam').sync_record(id=self.id, type='cancel')
        return res
