import logging

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

import json
import threading
import time
from datetime import datetime
from datetime import timedelta

import requests
from odoo import fields, models, api
from odoo.exceptions import ValidationError

from odoo.addons.restful.common import (get_redis)


class PhoneCall(models.Model):
    _inherit = 'crm.phone.call'

    def action_open_ticket(self):
        """ Open the website page with the survey form """
        self.ensure_one()
        if self.crm_id and self.crm_id.ticket_id:
            config = self.env['ir.config_parameter'].sudo()
            key = 'domain_caresoft_%s' % self.brand_id.code.lower()
            domain = config.get_param(key)
            domain = domain.replace('api', 'web55')
            domain = domain + '#/index?type=ticket&id=%s' % self.crm_id.ticket_id

            threaded_update_account = threading.Thread(target=self._update_account, args=([self.crm_id.id]))
            threaded_update_account.start()
            time.sleep(1)
            return {
                'type': 'ir.actions.act_url',
                'name': "Open ticket",
                'target': 'new',
                'url': domain
            }
        else:
            raise ValidationError("Không có Booking hoặc Booking của Phone call này không có ticket tương ứng!")

    def _update_account(self, id):
        try:
            # if 1 == 1:
            with api.Environment.manage():
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))
                booking = self.env['crm.lead'].browse(int(id))
                if booking:
                    brand_code = booking.brand_id.code.lower()
                    params = self.env['ir.config_parameter'].sudo()
                    domain_config = 'domain_caresoft_%s' % (brand_code)
                    token_config = 'domain_caresoft_token_%s' % (brand_code)

                    headers = {
                        'Authorization': 'Bearer ' + params.get_param(token_config),
                        'Content-Type': 'application/json'
                    }
                    # lấy thông tin acc
                    response = requests.get(
                        '%s/api/v1/tickets/%s' % (params.get_param(domain_config), booking.ticket_id), headers=headers)
                    response = response.json()
                    if 'ticket' in response and 'requester_id' in response['ticket'] and response['ticket'][
                        'requester_id']:
                        account_id = response['ticket']['requester_id']
                        # lấy thông tin account
                        response = requests.get(
                            '%s/api/v1/contacts/%s' % (params.get_param(domain_config), account_id), headers=headers)
                        response = response.json()
                        if response['code'] == 'ok':
                            if not response['contact']['phone_no2'] or response['contact']['phone_no3']:
                                if booking.mobile or booking.phone_no_3:
                                    data = {
                                        "contact": {
                                            "phone_no2": booking.mobile if booking.mobile else response['contact'][
                                                'phone_no2'],
                                            "phone_no3": booking.phone_no_3 if booking.phone_no_3 else
                                            response['contact']['phone_no3']
                                        }
                                    }
                                    response = requests.put(
                                        '%s/api/v1/contacts/%s' % (params.get_param(domain_config), account_id),
                                        headers=headers,
                                        data=json.dumps(data))
        except Exception as e:
            _logger.info('>' * 100)
            _logger.info(e)
            _logger.info('>' * 100)

    def create_ticket_phonecall(self):
        try:
            domain = [('active', '=', True), ('direction', '=', 'out'), ('ticket_id', '=', None),
                      ('call_date', '>=', datetime.now().date()),
                      ('call_date', '<', datetime.now().date() + timedelta(days=1)),
                      ('stage', 'in', ['draft', 'later', 'not_connect'])]
            data_phonecall = self.env['crm.phone.call'].search(domain)
            _logger.info("====================== data phone call =======================")
            _logger.info(data_phonecall)
            _logger.info("=================================================")
            Config = self.env['ir.config_parameter'].sudo()
            for item in data_phonecall:
                brand = item.brand_id
                domain_config = 'domain_caresoft_%s' % (brand.code.lower())
                token_config = 'domain_caresoft_token_%s' % (brand.code.lower())
                # get url & token of brand
                url = Config.get_param(domain_config)
                url = url + '/api/v1/tickets'
                token = Config.get_param(token_config)
                headers = {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                }
                sv = item.brand_id.config_phone_cs.filtered(
                    lambda r: r.care_type == item.care_type and r.type_crm_id.id == item.type_crm_id.id)
                type_ticket_pc = item.brand_id.custom_field_cs.filtered(lambda r: r.code_custom_field == 'type_ticket')
                pc_stage = item.brand_id.custom_field_cs.filtered(lambda r: r.code_custom_field == 'pc_stage')
                cs_service = item.brand_id.custom_field_cs.filtered(lambda r: r.code_custom_field == 'service')
                cs_service_code_dict = Config.get_param('cs_service_code_custom_fields_id_dict')
                cs_service_code_dict = eval(cs_service_code_dict)
                tp = []
                if item.service_id:
                    for s in item.service_id:
                        if s.default_code in cs_service_code_dict:
                            tp.append(cs_service_code_dict.get(s.default_code))
                else:
                    for s in item.crm_line_id:
                        if s.product_id.default_code in cs_service_code_dict:
                            tp.append(cs_service_code_dict.get(s.product_id.default_code))
                _logger.info("====================== cusstom field =======================")
                _logger.info(sv)
                _logger.info(type_ticket_pc)
                _logger.info(pc_stage)
                _logger.info("=================================================")
                if sv and type_ticket_pc and pc_stage:
                    data = {
                        "ticket": {
                            "ticket_subject": item.name,
                            "ticket_comment": "Create Phone Call",
                            "email": '',
                            "phone": item.phone,
                            "username": item.contact_name,
                            "ticket_status": "new",
                            "ticket_priority": "normal",
                            "ticket_source": "api",
                            "service_id": sv.service_id_care_soft,
                            "duedate": item.call_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                            "custom_fields": [
                                {
                                    "id": type_ticket_pc.custom_field_id,
                                    "value": type_ticket_pc.values.filtered(lambda r: r.code_value == 'pc').id_value,
                                },
                                # stage pc
                                {
                                    "id": pc_stage.custom_field_id,
                                    "value": pc_stage.values.filtered(lambda r: r.code_value == 'cxl').id_value,
                                },
                                # Dịch vụ chi tiết
                                {
                                    "id": cs_service.custom_field_id,
                                    "value": tuple(tp)
                                },
                            ]
                        }
                    }
                    _logger.info("====================== request =======================")
                    _logger.info(data)
                    _logger.info(headers)
                    _logger.info(url)
                    _logger.info("=================================================")
                    response = requests.post(url, data=json.dumps(data), headers=headers)
                    _logger.info("====================== response =======================")
                    _logger.info(response)
                    _logger.info("=================================================")
                    if response.status_code == 200:
                        response = response.json()
                        _logger.info("====================== json response =======================")
                        _logger.info(response)
                        _logger.info("=================================================")
                        item.write({
                            'ticket_id': response['ticket']['ticket_id']
                        })
        except Exception as e:
            log = self.env['api.log'].create({
                'name': 'API Case: get_ticket_case()',
                'content': e,
            })

    @api.model
    def create(self, vals_list):
        res = super(PhoneCall, self).create(vals_list)
        redis_client = get_redis()
        if redis_client:
            actions_phone_call_id = self.env.ref('crm_base.action_open_view_phone_call').id
            menu_phone_call_id = self.env.ref('crm_base.crm_menu_phone_call').id
            partner = self.env['res.partner'].sudo().search([('phone', '=', res.phone)], limit=1)
            if partner:
                key = res.phone
                datas = res.partner_id._get_phone_calls(partner, actions_phone_call_id, menu_phone_call_id)
                redis_client.hset(key, 'phone_calls', json.dumps(datas, indent=4, sort_keys=True, default=str))
        return res

    def write(self, values):
        res = super(PhoneCall, self).write(values)
        redis_client = get_redis()
        if redis_client:
            fields_change = ['call_date', 'name', 'state', 'support_rating', 'type_crm_id', 'active']
            actions_phone_call_id = self.env.ref('crm_base.action_open_view_phone_call').id
            menu_phone_call_id = self.env.ref('crm_base.crm_menu_phone_call').id
            if any(key in values for key in fields_change):
                partner = self.env['res.partner'].sudo().search([('phone', '=', self.phone)], limit=1)
                if partner:
                    key = self.phone
                    datas = self.partner_id._get_phone_calls(partner, actions_phone_call_id, menu_phone_call_id)
                    redis_client.hset(key, 'phone_calls', json.dumps(datas, indent=4, sort_keys=True, default=str))
        return res

    def view_customer_persona(self):
        domain = self.env['ir.config_parameter'].sudo().get_param('domain_customer_persona_extend')
        url = domain + '/app/customer-portrait/profile?company_id=%s&partner_id=%s' % (
            self.env.company.id, self.partner_id.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }



class ConfigPhoneCallCareSoft(models.Model):
    _name = 'config.phone.call.care.soft'
    _description = 'Config Phone Call CareSoft'

    name = fields.Char('Tên', compute='set_name_config_phone_call')
    type_crm_id = fields.Many2one('crm.type', string='Loại phone call', domain="[('phone_call','=',True)]",
                                  tracking=True)
    care_type = fields.Selection([('Spa', 'Spa'), ('Laser', 'Laser'), ('Odontology', 'Nha'), ('Surgery', 'Phẫu thuật'),
                                  ('DVKH', 'Dịch vụ khách hàng')], 'Đơn vị chăm sóc')
    brand_id = fields.Many2one('res.brand', string='Brand', tracking=True)
    # company_id = fields.Many2one('res.company', string='Company', tracking=True,
    #                              default=lambda self: self.env.company)
    service_id_care_soft = fields.Char('Service ID Care Soft')

    @api.depends('type_crm_id', 'care_type', 'brand_id')
    def set_name_config_phone_call(self):
        for rec in self:
            name = ''
            if rec.type_crm_id:
                name += str(rec.type_crm_id.name)
            if rec.care_type:
                name += ' -' + str(rec.care_type)
            if rec.brand_id:
                name += ' -' + str(rec.brand_id.name)
            rec.name = name
