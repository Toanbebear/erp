import json
import logging

import requests
from odoo.addons.queue_job.job import job

from odoo import models, api, fields

_logger = logging.getLogger(__name__)


class CRMLeadInherit(models.Model):
    _inherit = 'crm.lead'

    # birth_month = fields.Selection(
    #     [('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
    #      ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'), ('11', 'Tháng 11'),
    #      ('12', 'Tháng 12')], string='Tháng sinh', compute='_birth_month', store=True)
    birth_month = fields.Selection(
        [('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'), ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
         ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'), ('10', 'Tháng 10'), ('11', 'Tháng 11'),
         ('12', 'Tháng 12')], string='Tháng sinh')
    @api.depends('birth_date')
    def _birth_month(self):
        for rec in self:
            if not rec.birth_month and rec.birth_date:
                rec.birth_month = str(rec.birth_date.month)

    @job
    def sync_record_seeding(self, id, type):
        crm_lead = self.sudo().browse(id)

        config = self.env['ir.config_parameter'].sudo()
        code_sources = eval(config.get_param('check_source_code_sync_mkt'))
        utm_source = self.env['utm.source'].sudo().search([('code', 'in', code_sources)])
        if crm_lead.source_id in utm_source and crm_lead.ticket_id:
            # if crm_lead.source_id == utm_source:
            line_ids = []
            for line in crm_lead.crm_line_ids:
                value = {
                    "his_service_id": line.product_id.default_code,
                    "stage": line.stage,
                    "odontology": line.odontology,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "discount_percent": line.discount_percent,
                    "discount_cash": line.discount_cash,
                    "sale_to": line.sale_to,
                    "total_before_discount": line.total_before_discount,
                    'total': line.total,
                    "erp_id": line.id
                }
                line_ids.append(value)
            config = self.env['ir.config_parameter'].sudo()
            token = config.get_param('token_seeding')
            url_root = config.get_param('url_seeding')
            if crm_lead.type == 'lead':
                body = {
                    "erp_id": id,
                    "name": crm_lead.name,
                    "customer_classification": crm_lead.customer_classification,
                    "phone_1": crm_lead.phone,
                    "phone_2": crm_lead.mobile,
                    "contact_name": crm_lead.contact_name,
                    "sex": crm_lead.gender,
                    "city_id": crm_lead.state_id.code,
                    "country_id": crm_lead.country_id.code,
                    "category_source_id": crm_lead.category_source_id.code,
                    "source_id": crm_lead.source_id.code,
                    "type_data_partner": crm_lead.type_data_partner,
                    "company_id": crm_lead.company_id.code,
                    "price_list_id": "1",
                    "check": "seeding",
                    "stage_id": crm_lead.stage_id.id,
                    "line_ids": line_ids,
                    "note": crm_lead.note if crm_lead.note else '',
                    "id_ticket": crm_lead.ticket_id,
                    "sale_create": crm_lead.create_by.name if crm_lead.create_by.name else '',
                }
                if type == 'create':
                    url = url_root + '/api/v1/create-lead'
                else:
                    url = url_root + '/api/v1/update-lead'

            else:
                body = {
                    'erp_id': id,
                    "name": crm_lead.name,
                    "customer_classification": crm_lead.customer_classification,
                    "phone_1": crm_lead.phone,
                    "phone_2": crm_lead.mobile,
                    "contact_name": crm_lead.contact_name,
                    "sex": crm_lead.gender,
                    "city_id": crm_lead.state_id.code,
                    "country_id": crm_lead.country_id.code,
                    "category_source_id": crm_lead.category_source_id.code,
                    "source_id": crm_lead.source_id.code,
                    "stage_id": crm_lead.stage_id.id,
                    "type_data_partner": crm_lead.type_data_partner,
                    "booking_date": str(crm_lead.booking_date),
                    "expected_day": str(crm_lead.expected_day),
                    "effect": crm_lead.effect,
                    "day_expire": str(crm_lead.day_expire),
                    "custom_come": crm_lead.customer_come,
                    "company_id": crm_lead.company_id.code,
                    "price_list_id": "23",
                    "check": "seeding",
                    "line_ids": line_ids,
                    "note": crm_lead.note if crm_lead.note else '',
                    "id_ticket": crm_lead.ticket_id,
                    "sale_create": crm_lead.create_by.name if crm_lead.create_by.name else '',
                }
                if type == 'create':
                    url = url_root + '/api/v1/create-booking'
                    seeding_booking = self.env['seeding.booking'].sudo().search([('crm_id', '=', int(id))])
                    user_seeding = ''
                    if seeding_booking:
                        user_seeding = seeding_booking.seeding_user_id.code_user
                    body['user_seeding'] = user_seeding
                else:
                    url = url_root + '/api/v1/update-booking'
            headers = {
                'access-token': token,
                'Content-Type': 'application/json'
            }

            response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)
            response = response.json()

    @api.model
    def create(self, vals):
        res = super(CRMLeadInherit, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_seeding_crm_lead').sync_record_seeding(id=res.id,
                                                                                                    type='create')
        return res

    def write(self, vals):
        res = super(CRMLeadInherit, self).write(vals)
        if res:
            for crm in self:
                if crm.id:
                    crm.sudo().with_delay(priority=0, channel='sync_seeding_crm_lead').sync_record_seeding(id=crm.id,
                                                                                                           type='write')
        return res
