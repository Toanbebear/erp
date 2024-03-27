import json
import logging

import requests
from odoo.addons.queue_job.job import job

from odoo import models, api, fields

_logger = logging.getLogger(__name__)


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    @job
    def sync_record(self, id):
        config = self.env['ir.config_parameter'].sudo()
        token = config.get_param('token_seeding')
        url_root = config.get_param('url_seeding')
        code_sources = eval(config.get_param('check_source_code_sync_mkt'))
        utm_source = self.env['utm.source'].sudo().search([('code', 'in', code_sources)])
        sale_order_line = self.sudo().browse(id)
        # if sale_order_line.order_id and sale_order_line.order_id.booking_id.source_id == utm_source and sale_order_line.order_id.booking_id.ticket_id:
        if sale_order_line.order_id and sale_order_line.order_id.booking_id.source_id in utm_source:
            url = url_root + "/api/v1/sync-seeding-sale-order-line"
            service = self.env['sh.medical.health.center.service'].sudo().search(
                [('product_id', '=', sale_order_line.product_id.id)])
            body = {
                'erp_id': sale_order_line.id,
                'sale_order': sale_order_line.order_id.id,
                'service': service.default_code,
                'price_subtotal': sale_order_line.price_subtotal,
                'brand_id': sale_order_line.order_id.brand_id.code
            }
            headers = {
                'access-token': token,
                'Content-Type': 'application/json'
            }
            response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)
            response = response.json()

    @api.model
    def create(self, vals):
        res = super(SaleOrderLineInherit, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_seeding_sale_order_line').sync_record(id=res.id)
        return res

    def write(self, vals):
        res = super(SaleOrderLineInherit, self).write(vals)
        if res:
            for sol in self:
                if sol.id:
                    sol.sudo().with_delay(priority=0, channel='sync_seeding_sale_order_line').sync_record(id=sol.id)
        return res


