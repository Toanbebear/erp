import json
import logging

import requests
from odoo.addons.queue_job.job import job

from odoo import models, api

_logger = logging.getLogger(__name__)


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    @job
    def sync_record(self, id, type):
        config = self.env['ir.config_parameter'].sudo()
        token = config.get_param('token_seeding')
        url_root = config.get_param('url_seeding')
        sale_order = self.sudo().browse(id)
        code_sources = eval(config.get_param('check_source_code_sync_mkt'))
        utm_source = self.env['utm.source'].sudo().search([('code', 'in', code_sources)])
        if sale_order.booking_id.source_id in utm_source and sale_order.booking_id.ticket_id:
        # if sale_order.booking_id.source_id == utm_source:
            body = {
                "name": sale_order.name,
                "booking_id": sale_order.booking_id.name,
                "code_customer": sale_order.code_customer,
                "phone_customer": sale_order.phone_customer,
                "date_order": str(sale_order.date_order),
                "price_list_type": sale_order.pricelist_type,
                "price_list_id": "1",
                "amount_remain": sale_order.amount_remain,
                "amount_owed": sale_order.amount_owed,
                "source_id": sale_order.booking_id.source_id.code,
                "state": sale_order.state,
                "erp_id": id,
                "check": "seeding",
                "amount_total": sale_order.amount_total
            }
            if type == 'create':
                url = url_root + "/api/v1/create-seeding-sale-order"
            else:
                url = url_root + "/api/v1/update-seeding-sale-order"
            headers = {
                'access-token': token,
                'Content-Type': 'application/json'
            }
            response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)
            response = response.json()

    @api.model
    def create(self, vals):
        res = super(SaleOrderInherit, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_seeding_sale_order').sync_record(id=res.id, type='create')
        return res

    def write(self, vals):
        res = super(SaleOrderInherit, self).write(vals)
        if res:
            for so in self:
                if so.id:
                    so.sudo().with_delay(priority=0, channel='sync_seeding_sale_order').sync_record(
                        id=so.id, type='write')
        return res
