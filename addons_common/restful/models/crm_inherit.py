import json
import logging
from datetime import datetime
from odoo.exceptions import ValidationError
import threading
import requests
import time
from odoo import fields, models, api
from odoo.addons.restful.common import (
    get_redis
)

_logger = logging.getLogger(__name__)


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    rest_api = fields.Boolean('Rest API', default=False)


class UtmSource(models.Model):
    _inherit = 'utm.source'

    id_kn = fields.Integer('ID KN CS')
    id_da = fields.Integer('ID DA CS')
    id_hh = fields.Integer('ID HH CS')
    id_pr = fields.Integer('ID PR CS')
    id_hv = fields.Integer('ID Academy CS')
    id_rh = fields.Integer('ID Richard CS')

    def write(self, values):
        res = super(UtmSource, self).write(values)
        if any(key in values for key in ['name', 'category_id', 'code', 'active']):
            self.recache()
        return res

    @api.model
    def create(self, values):
        res = super(UtmSource, self).create(values)
        self.recache()
        return res

    def unlink(self):
        res = super(UtmSource, self).unlink()
        self.recache()
        return res

    def recache(self):
        """
            recache
        """
        redis_client = get_redis()
        if redis_client:
            redis_client.set(self.get_key(),
                             json.dumps(self.get_data(), indent=4, sort_keys=True, default=str))

    def get_data(self):
        domain = [('active', '=', True)]
        fields = ['id', 'name', 'code', 'category_id']
        sources = self.env['utm.source'].search_read(domain, fields)
        for item in sources:
            category_id = item['category_id']
            if isinstance(category_id, tuple):
                item['category_id'] = category_id[0]
                item['category_name'] = category_id[1]
        return sources

    def get_key(self):
        return "utm_source"

    def api_get_data(self, offset=0, limit=None, order=None):
        key = self.get_key()
        # Phân trang thì lấy luôn trong db
        if not offset:
            redis_client = get_redis()
            if redis_client:
                data = redis_client.get(key)
                if data:
                    return json.loads(data)

        result = self.get_data()
        if result:
            # Khi không phân trang mới set vào cache, còn phân trang tính sau
            if not offset:
                if redis_client:
                    redis_client.set(key, json.dumps(result, indent=4, sort_keys=True, default=str))
        return result


class PainPointsAndDesires(models.Model):
    _inherit = 'pain.point.and.desires'

    lead_id = fields.Many2one('crm.lead', string='Lead')
    phone = fields.Char('SĐT')


class CrmCase(models.Model):
    _inherit = 'crm.case'

    ticket_id = fields.Integer('Case ticket id')

    def write(self, values):
        res = super(CrmCase, self).write(values)
        redis_client = get_redis()
        if redis_client:
            case_action_id = self.env.ref('crm_base.action_complain_case_view').id
            case_menu_id = self.env.ref('crm_base.crm_menu_case').id
            partner = self.env['res.partner'].sudo().search([('phone', '=', self.phone)], limit=1)
            if partner:
                key = self.phone
                datas = self.partner_id._get_cases(partner, case_action_id, case_menu_id)
                redis_client.hset(key, 'cases', json.dumps(datas, indent=4, sort_keys=True, default=str))
        return res


class CancelCRMLine(models.TransientModel):
    _inherit = 'crm.line.cancel'
    _description = 'Cancel CRM Line'

    def cancel_crm_line(self):
        res = super(CancelCRMLine, self).cancel_crm_line()
        try:
            # if 1 == 1:
            params = self.env['ir.config_parameter'].sudo()
            check_sync = params.get_param('config_sync_data_care_soft')
            if check_sync.lower() == 'true':
                for rec in self:
                    if rec.crm_line_id.crm_id.type == 'opportunity' and rec.crm_line_id.crm_id.ticket_id:
                        domain_config = 'domain_caresoft_%s' % (rec.crm_line_id.crm_id.brand_id.code.lower())
                        token_config = 'domain_caresoft_token_%s' % (rec.crm_line_id.crm_id.brand_id.code.lower())
                        author_config = 'config_author_id_care_soft_%s' % (rec.crm_line_id.crm_id.brand_id.code.lower())

                        token = params.get_param(token_config)
                        author_id = params.get_param(author_config)

                        service_id_care_soft_config = 'config_service_care_soft_%s' % (
                            rec.crm_line_id.crm_id.brand_id.code.lower())
                        config_service_id_care_soft = params.get_param(service_id_care_soft_config)

                        # get url of brand
                        url = params.get_param(domain_config)

                        headers = {
                            'Authorization': 'Bearer ' + token,
                            'Content-Type': 'application/json'
                        }

                        list_service_erp = ','
                        list_service_cs = eval(params.get_param('cs_service_code_custom_fields_id_dict'))
                        for crm_line in rec.crm_line_id.crm_id.crm_line_ids:
                            if crm_line.stage != 'cancel':
                                code_service = crm_line.service_id.default_code.replace('Đ', 'D')
                                list_service_erp = list_service_erp + str(list_service_cs['%s' % code_service]) + ','

                        data = {
                            "ticket": {
                                "ticket_comment": {
                                    "body": "Cập nhật dịch vụ Booking",
                                    "author_id": int(author_id),
                                    "type": 0,
                                    "is_public": 1
                                },
                                "custom_fields": [
                                    {
                                        "id": int(config_service_id_care_soft),
                                        "value": list_service_erp
                                    },
                                ]
                            }
                        }
                        response = requests.put('%s/api/v1/tickets/%s' % (url, rec.crm_line_id.crm_id.ticket_id),
                                                headers=headers,
                                                data=json.dumps(data))
        except Exception as e:
            _logger.info('============================= update ticket error - crm line ==============================')
            _logger.info(e)
            _logger.info('===========================================================================================')
            pass
        return res


class PartnerQualify(models.TransientModel):
    _inherit = 'check.partner.qualify'

    def qualify(self):
        res = super(PartnerQualify, self).qualify()
        booking = self.env['crm.lead'].browse(int(res['res_id']))
        if booking and booking.partner_id and self.lead_id:
            lead = self.lead_id
            partner = booking.partner_id
            lead.desires.write({'partner_id': partner.id})
            lead.pain_point.write({'partner_id': partner.id})
        return res

