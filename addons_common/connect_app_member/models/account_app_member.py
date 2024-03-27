import json
import logging
from datetime import datetime
import requests
from odoo.addons.queue_job.job import job
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class AccountAppMember(models.Model):
    _name = 'account.app.member'
    _description = 'Tài khoản khách hàng'

    phone = fields.Char('Số điện thoại Account')
    name = fields.Char('Tên khách hàng của Account')
    partner_id = fields.Many2one('res.partner', 'Khách hàng gán với Account')

    def cron_job_sync_account_da(self):
        params = self.env['ir.config_parameter'].sudo()
        domain = params.get_param('config_domain_app_member_da')
        token = params.get_param('config_token_app_member_da')
        url = domain + "/api/v1/get-account"
        payload = {}
        headers = {
            'Authorization': token,
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        response = response.json()
        datas = response['data']
        for data in datas:
            partner = self.env['res.partner'].sudo().search(
                ['|', ('phone', '=', data['phone']), ('mobile', '=', data['phone'])])
            value = {
                'phone': data['phone'],
                'name': data['name'],
                'partner_id': partner.id if partner else None
            }
            account = self.env['account.app.member'].sudo().search([('phone', '=', data['phone'])])
            if account:
                account.sudo().write(value)
            else:
                self.env['account.app.member'].sudo().create(value)


class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    @job
    def sync_record(self, id):
        partner = self.env['res.partner'].sudo().browse(id)
        params = self.env['ir.config_parameter'].sudo()
        config_domain_da = params.get_param('config_domain_app_member_da')
        config_domain_kn = params.get_param('config_domain_app_member_kn')
        config_domain_pr = params.get_param('config_domain_app_member_pr')
        config_token_da = params.get_param('config_token_app_member_da')
        config_token_kn = params.get_param('config_token_app_member_kn')
        config_token_pr = params.get_param('config_token_app_member_pr')
        config_sync_da = params.get_param('sync_app_member_da')
        config_sync_kn = params.get_param('sync_app_member_kn')
        config_sync_pr = params.get_param('sync_app_member_pr')
        if config_sync_da == 'True':
            if config_domain_da and config_token_da:
                body = {
                    'id': partner.id,
                    'name': partner.name if partner.name else None,
                    'phone': partner.phone if partner.phone else None,
                    'mobile': partner.mobile if partner.mobile else None,
                }
                url = config_domain_da + '/api/v1/sync-account'
                headers = {
                    'Authorization': config_token_da,
                    'Content-Type': 'application/json'
                }
                response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)
        if config_sync_kn == 'True':
            if config_domain_kn and config_token_kn:
                body = {
                    'id': partner.id,
                    'name': partner.name if partner.name else None,
                    'phone': partner.phone if partner.phone else None,
                    'mobile': partner.mobile if partner.mobile else None,
                }
                url = config_domain_kn + '/api/v1/sync-account'
                headers = {
                    'Authorization': config_token_kn,
                    'Content-Type': 'application/json'
                }
                response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)
        if config_sync_pr == 'True':
            if config_domain_pr and config_token_pr:
                body = {
                    'id': partner.id,
                    'name': partner.name if partner.name else None,
                    'phone': partner.phone if partner.phone else None,
                    'mobile': partner.mobile if partner.mobile else None,
                }
                url = config_domain_pr + '/api/v1/sync-account'
                headers = {
                    'Authorization': config_token_pr,
                    'Content-Type': 'application/json'
                }
                response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)

    def write(self, vals):
        res = super(InheritResPartner, self).write(vals)
        if res:
            for rec in self:
                if rec.id:
                    rec.sudo().with_delay(priority=0, channel='sync_app_member_account').sync_record(id=rec.id)
        return res

    @api.model
    def create(self, vals):
        res = super(InheritResPartner, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_app_member_account').sync_record(id=res.id)
        return res


class InheritSaleOrder(models.Model):
    _inherit = "sale.order"

    @job
    def sync_record_history_point(self, id):
        data = []
        sale_order = self.sudo().browse(id)
        brand = sale_order.brand_id.code
        params = self.env['ir.config_parameter'].sudo()
        config_sync = 'sync_app_member_%s' % brand.lower()
        config_domain = 'config_domain_app_member_%s' % brand.lower()
        config_token = 'config_token_app_member_%s' % brand.lower()
        domain = params.get_param(config_domain)
        token = params.get_param(config_token)
        sync = params.get_param(config_sync)
        if brand.lower() != 'da' and sync == 'True':
            if domain and token:
                for order_line in sale_order.order_line:
                    for rec in order_line:
                        value = {
                            'name': rec.product_id.name,
                            'id_service': rec.product_id.id,
                            'order_line_id': rec.id,
                            'so': sale_order.name,
                            'date': sale_order.date_order,
                            'price': rec.price_subtotal,
                            'phone': sale_order.phone_customer
                        }
                        data.append(value)
                url = domain + '/api/v1/sync-history-point'
                headers = {
                    'Authorization': token,
                    'Content-Type': 'application/json'
                }
                response = requests.request('POST', url=url, data=json.dumps(data), headers=headers)

    def write(self, vals):
        res = super(InheritSaleOrder, self).write(vals)
        if res:
            for order in self:
                if order.id:
                    order.sudo().with_delay(priority=0,
                                            channel='sync_app_member_history_point').sync_record_history_point(
                        id=order.id)
        return res

    @api.model
    def create(self, vals):
        res = super(InheritSaleOrder, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_app_member_history_point').sync_record_history_point(
                id=res.id)
        return res
