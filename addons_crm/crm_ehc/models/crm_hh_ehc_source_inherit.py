import json

from odoo import fields, api, models
import requests
import logging
from odoo.addons.crm_ehc.models.ehc_common import get_token_ehc, get_url_ehc, get_api_code_ehc

_logger = logging.getLogger(__name__)


class UtmSourceCategory(models.Model):
    _inherit = 'crm.category.source'

    sync_ehc = fields.Boolean('Sync EHC', default=False)

    def post_ctg_source_to_ehc(self):
        token = get_token_ehc()
        url = get_url_ehc()
        api_code = get_api_code_ehc()

        url = url + '/api/about/group?api=%s' % api_code

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token,
        }
        name = '[' + self.code + ']' + self.name
        payload = {
            "source_group_user_code": self.code,
            "source_group_user_name": name,
            "stage": "0"
        }

        r = requests.request("POST", url=url, data=json.dumps(payload), headers=headers)
        response = r.json()
        _logger.info("===============")
        _logger.info("payload: %s" % payload)
        _logger.info("response: %s" % response)
        if 'status' in response and response['status'] == '0':
            self.sync_ehc = True


class UtmSource(models.Model):
    _inherit = 'utm.source'

    sync_ehc = fields.Boolean('Sync EHC', default=False)

    def post_source_to_ehc(self, ctg_source):
        token = get_token_ehc()
        url = get_url_ehc()
        api_code = get_api_code_ehc()

        url = url + '/api/about?api=%s' % api_code

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token,
        }

        payload = {
            "source_user_code": ctg_source.code,
            "source_user_name": ctg_source.name,
            "source_user_phone": '',
            "source_user_address": "",
            "source_user_bank_account": '',
            "source_group_user_code": ctg_source.category_id.code,
            "source_user_note": '',
            "stage": "0"
        }

        r = requests.request("POST", url=url, data=json.dumps(payload), headers=headers)
        response = r.json()
        _logger.info("===============")
        _logger.info("payload: %s" % payload)
        _logger.info("response: %s" % response)
        if 'status' in response and response['status'] == '0':
            ctg_source.sync_ehc = True

    def button_post_source_to_ehc(self):
        self.post_source_to_ehc(ctg_source=self)

    def cron_post_source_to_ehc(self):
        sources = self.env['utm.source'].search([('sync_ehc', '=', False), ('brand_id.code', '=', 'HH')])
        for source in sources:
            self.post_source_to_ehc(ctg_source=source)


class UtmSourceCtv(models.Model):
    _inherit = 'crm.collaborators'

    sync_ehc = fields.Boolean('Sync EHC', default=False)
    ehc_category_source_id = fields.Many2one('crm.category.source', string='Nhóm nguồn ERP',
                                             domain="[('code', 'in', ['CTV', 'TPM'])]")
    ehc_source_id = fields.Many2one('utm.source', string='Nguồn ERP', domain="[('category_id','=',ehc_category_source_id)]")
    source_map = fields.Many2one('crm.hh.ehc.utm.source', string='Nguồn EHC')
    log = fields.Text('Log')
    address_ehc = fields.Text('Địa chỉ')

    check_ehc = fields.Boolean('CTV EHC', default=False)

    @api.onchange('ehc_category_source_id')
    def onchange_ehc_category_source_id(self):
        for rec in self:
            if rec.ehc_category_source_id:
                rec.category_source_id = rec.ehc_category_source_id.id
                data_domain = self.env['crm.hh.ehc.map.utm.source'].sudo().search([('erp_source', '=', rec.ehc_category_source_id.id)], limit=1)
                if data_domain:
                    return {
                        'domain': {'source_map': [('id', 'in', data_domain.ehc_source.ids)]}
                    }

    @api.onchange('ehc_source_id')
    def onchange_ehc_source_id(self):
        for rec in self:
            if rec.ehc_source_id:
                rec.source_id = rec.ehc_source_id.id

    def cron_post_source_ctv_to_ehc(self):
        token = get_token_ehc()
        url = get_url_ehc()
        api_code = get_api_code_ehc()

        url = url + '/api/about?api=%s' % api_code

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token,
        }
        ctv_ids = self.env['crm.collaborators'].search([('check_ehc', '=', True)])
        for ctv_id in ctv_ids:
            bank = ''
            if ctv_id.bank and ctv_id.card_number:
                bank = ctv_id.bank + '-' + ctv_id.card_number

            payload = {
                "source_user_code": ctv_id.code_collaborators,
                "source_user_name": ctv_id.collaborators,
                "source_user_phone": ctv_id.phone,
                "source_user_address": ctv_id.address_ehc,
                "source_user_bank_account": bank,
                # "source_group_user_code": ctv_id.ehc_source_id.code,
                "source_group_user_code": self.source_map.code if self.source_map else self.ehc_category_source_id.code,
                "source_user_note": ctv_id.note,
                "stage": "0"
            }

            r = requests.request("POST", url=url, data=json.dumps(payload), headers=headers)
            response = r.json()
            ctv_id.log = response
            _logger.info("===============")
            _logger.info("payload: %s" % payload)
            _logger.info("response: %s" % response)
            if 'status' in response and response['status'] == '0':
                ctv_id.sync_ehc = True

    def post_source_ctv_to_ehc(self):
        token = get_token_ehc()
        url = get_url_ehc()
        api_code = get_api_code_ehc()

        url = url + '/api/about?api=%s' % api_code

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token,
        }
        bank = ''
        if self.bank and self.card_number:
            bank = self.bank + '-' + self.card_number

        payload = {
            "source_user_code": self.code_collaborators,
            "source_user_name": self.collaborators,
            "source_user_phone": self.phone,
            "source_user_address": self.address_ehc,
            "source_user_bank_account": bank,
            # "source_group_user_code": self.ehc_source_id.code,
            "source_group_user_code": self.source_map.code if self.source_map else self.ehc_category_source_id.code,
            "source_user_note": self.note,
            "stage": "0"
        }

        r = requests.request("POST", url=url, data=json.dumps(payload), headers=headers)
        response = r.json()
        self.log = response
        _logger.info("===============")
        _logger.info("payload: %s" % payload)
        _logger.info("response: %s" % response)
        if 'status' in response and response['status'] == '0':
            self.sync_ehc = True
