import json
import logging

import requests
from odoo.addons.queue_job.job import job

from odoo import models, api

_logger = logging.getLogger(__name__)


class CrmSalePaymentInherit(models.Model):
    _inherit = 'crm.sale.payment'

    @job
    def sync_record(self, id):
        config = self.env['ir.config_parameter'].sudo()
        token = config.get_param('token_seeding')
        url_root = config.get_param('url_seeding')
        code_sources = eval(config.get_param('check_source_code_sync_mkt'))
        utm_source = self.env['utm.source'].sudo().search([('code', 'in', code_sources)])
        crm_sale_payment = self.sudo().browse(id)
        if crm_sale_payment.booking_id and crm_sale_payment.booking_id.source_id in utm_source and crm_sale_payment.booking_id.ticket_id:
        # if crm_sale_payment.booking_id and crm_sale_payment.booking_id.source_id == utm_source:
            url = url_root + "/api/v1/sync-crm-sale-payment"
            body = {
                'id_erp': crm_sale_payment.id,
                'booking_id': crm_sale_payment.booking_id.id,
                'service': crm_sale_payment.service_id.default_code if crm_sale_payment.service_id else None,
                'company_id': crm_sale_payment.company_id.code if crm_sale_payment.company_id else None,
                'brand_id': crm_sale_payment.company_id.brand_id.code if crm_sale_payment.company_id else None,
                'payment_date': str(crm_sale_payment.payment_date) if crm_sale_payment.payment_date else None,
                'amount_process': crm_sale_payment.amount_proceeds
            }
            headers = {
                'access-token': token,
                'Content-Type': 'application/json'
            }
            response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)
            response = response.json()

    @api.model
    def create(self, vals):
        res = super(CrmSalePaymentInherit, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_seeding_crm_sale_payment').sync_record(id=res.id)
        return res

    def write(self, vals):
        res = super(CrmSalePaymentInherit, self).write(vals)
        if res:
            for sp in self:
                if sp.id:
                    sp.sudo().with_delay(priority=0, channel='sync_seeding_crm_sale_payment').sync_record(id=sp.id)
        return res
