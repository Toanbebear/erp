import json
import logging

import requests
from odoo.addons.queue_job.job import job

from odoo import models, api

_logger = logging.getLogger(__name__)


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    @job
    def sync_record(self, id, type):
        config = self.env['ir.config_parameter'].sudo()

        code_sources = eval(config.get_param('check_source_code_sync_mkt'))
        token = config.get_param('token_seeding')
        url_root = config.get_param('url_seeding')
        account_payment = self.sudo().browse(id)
        utm_source = self.env['utm.source'].sudo().search([('code', 'in', code_sources)])
        if account_payment.crm_id and account_payment.crm_id.source_id in utm_source and account_payment.crm_id.ticket_id:
        # if account_payment.crm_id and account_payment.crm_id.source_id == utm_source:
            val = []
            for service in account_payment.service_ids:
                value = {'code_group_service': service.crm_line_id.service_id.service_category.code,
                         'total': service.prepayment_amount,
                         'id_erp': service.id,
                         'brand_id': service.company_id.brand_id.code}
                val.append(value)
            body = {
                    "name": str(account_payment.name),
                    "payment_type": account_payment.payment_type,
                    "internal_payment_type": account_payment.internal_payment_type,
                    "payment_method": str(account_payment.payment_method),
                    "partner_type": account_payment.partner_type,
                    "patient": "nam123",
                    "booking_id": account_payment.crm_id.name,
                    "format_phone": account_payment.format_phone,
                    "amount": account_payment.amount,
                    "amount_vnd": account_payment.amount_vnd,
                    "text_total": account_payment.text_total,
                    "payment_date": str(account_payment.payment_date),
                    "communication": account_payment.communication,
                    "journal_id": "Sổ nhật ký",
                    "transfer_payment_id": "Phiếu điều chuyển",
                    "erp_id": id,
                    "state": account_payment.state,
                    "check": "seeding",
                    "service_ids": val,
                }
            if type == 'create':
                url = url_root + "/api/v1/create-seeding-account-payment"
            else:
                url = url_root + "/api/v1/update-seeding-account-payment"
            headers = {
                'access-token': token,
                'Content-Type': 'application/json'
            }
            response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)
            response = response.json()

    @api.model
    def create(self, vals):
        res = super(AccountPaymentInherit, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_seeding_account_payment').sync_record(id=res.id,
                                                                                                   type='create')
        return res

    def write(self, vals):
        res = super(AccountPaymentInherit, self).write(vals)
        if res:
            for ap in self:
                if ap.id:
                    ap.sudo().with_delay(priority=0, channel='sync_seeding_account_payment').sync_record(id=ap.id,
                                                                                                     type='write')
        return res
