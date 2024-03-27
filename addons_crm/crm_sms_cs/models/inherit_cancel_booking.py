import json
import logging
from datetime import datetime, timedelta

import requests

from odoo import api, tools
from odoo import models, fields

_logger = logging.getLogger(__name__)


class InheritCrmLead(models.TransientModel):
    _inherit = 'cancel.booking'

    def set_cancel(self):
        res = super(InheritCrmLead, self).set_cancel()
        config = self.env['ir.config_parameter'].sudo()
        for rec in self:
            if rec.booking_id:
                self.delete_sms_booking_cancel_or_outsold(booking_id=rec.booking_id)
                if rec.booking_id.type == 'opportunity' and rec.booking_id.customer_come == 'yes':
                    # lấy nội dung tin nhắn theo thương hiệu
                    key_sms_content = 'sms_survey_content_%s' % (rec.booking_id.company_id.brand_id.code.lower())
                    sms_content = config.get_param(key_sms_content)

                    # lấy link khảo sát bk cancel theo thương hiệu
                    key_link_survey = 'sms_survey_link_cancel_%s' % (rec.booking_id.company_id.brand_id.code.lower())
                    link_survey = config.get_param(key_link_survey)

                    # set ngày gửi SMS: 9h ngày hôm sau (sau ngày KH cancel bk)
                    send_date = datetime.now()
                    send_date = send_date + timedelta(days=1)
                    send_date = send_date.replace(hour=2, minute=0, second=0)
                    if sms_content and link_survey:
                        sms_content = sms_content.replace('[LINK]', link_survey)
                        sms = self.env['crm.sms'].sudo().create({
                            'name': "SMS Khảo sát Khách hàng Cancel Booking",
                            'partner_id': rec.booking_id.partner_id.id,
                            'contact_name': rec.booking_id.partner_id.name,
                            'phone': rec.booking_id.phone,
                            'company_id': rec.booking_id.company_id.id,
                            'company2_id': [(6, 0, rec.booking_id.company2_id.ids)] if rec.booking_id else None,
                            'crm_id': rec.booking_id.id if rec.booking_id else None,
                            'send_date': send_date,
                            'desc': sms_content,
                        })
        return res

    def set_out_sold(self):
        res = super(InheritCrmLead, self).set_out_sold()
        config = self.env['ir.config_parameter'].sudo()
        for rec in self:
            if rec.booking_id:
                self.delete_sms_booking_cancel_or_outsold(booking_id=rec.booking_id)
                if rec.booking_id.type == 'opportunity':
                    # lấy nội dung tin nhắn theo thương hiệu
                    key_sms_content = 'sms_survey_content_%s' % (rec.booking_id.company_id.brand_id.code.lower())
                    sms_content = config.get_param(key_sms_content)

                    # lấy link khảo sát bk OS theo thương hiệu
                    key_link_survey = 'sms_survey_link_os_%s' % (rec.booking_id.company_id.brand_id.code.lower())
                    link_survey = config.get_param(key_link_survey)

                    # set ngày gửi SMS: 9h ngày hôm sau (sau ngày KH cancel bk)
                    send_date = datetime.now()
                    send_date = send_date + timedelta(days=1)
                    send_date = send_date.replace(hour=2, minute=0, second=0)
                    if sms_content and link_survey:
                        sms_content = sms_content.replace('[LINK]', link_survey)
                        sms = self.env['crm.sms'].sudo().create({
                            'name': "SMS Khảo sát Booking OutSold",
                            'partner_id': rec.booking_id.partner_id.id,
                            'contact_name': rec.booking_id.partner_id.name,
                            'phone': rec.booking_id.phone,
                            'company_id': rec.booking_id.company_id.id,
                            'company2_id': [(6, 0, rec.booking_id.company2_id.ids)] if rec.booking_id else None,
                            'crm_id': rec.booking_id.id if rec.booking_id else None,
                            'send_date': send_date,
                            'desc': sms_content,
                        })
        return res

    def send_sms_survey(self):
        config = self.env['ir.config_parameter'].sudo()
        # Lấy account thương hiệu và token bên caresoft
        cs_account = {}
        brands = self.env['res.brand'].search([])
        for brand in brands:
            cs_account[brand.id] = {
                'domain': config.get_param('domain_caresoft_%s' % (brand.code.lower())),
                'token': config.get_param('domain_caresoft_token_%s' % (brand.code.lower())),
                'service_id': config.get_param('domain_caresoft_service_id_%s' % (brand.code.lower()))
            }

        start_time = datetime.now().replace(hour=9, minute=0, second=0) - timedelta(minutes=10)
        end_time = datetime.now().replace(hour=9, minute=0, second=0) + timedelta(minutes=10)

        sms_lines = self.env['crm.sms'].search([('active', '=', True),
                                                ('state', '=', 'draft'),
                                                ('send_date', '>=', start_time),
                                                ('send_date', '<=', end_time),
                                                ('phone', '!=', False),
                                                ('desc', '!=', False)],
                                               order='send_date asc')

        for sms in sms_lines:
            brand_id = sms.brand_id.id
            if brand_id in cs_account:
                domain = cs_account[brand_id]['domain']
                service_id = cs_account[brand_id]['service_id']
                token = cs_account[brand_id]['token']
                content = sms.desc
                phone = sms.phone
                if phone and content:
                    res = self._sms_cs(domain, token, service_id, content, phone)
                    if res['code'] == 'ok':
                        sms.write({
                            'state': 'sent',
                            'cs_response': json.dumps(res),
                        })
                    else:
                        sms.write({
                            'state': 'error',
                            'cs_response': json.dumps(res),
                        })

    def _sms_cs(self, domain, token, service_id, content, phone):

        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }

        data = {
            "sms": {
                "service_id": service_id,
                "content": content,
                "phone": phone,
            }
        }

        url = "%s/api/v1/sms" % domain
        _logger.info("Send headers %s data %s", headers, data)

        res = requests.post(url, headers=headers, data=json.dumps(data))
        _logger.info("Response %s", res)

        if res.status_code == 200:
            return json.loads(res.content.decode())
        else:
            return {'code': 'error'}

    def delete_sms_booking_cancel_or_outsold(self, booking_id):
        sms_lines = self.env['crm.sms'].sudo().search([('crm_id', '=', booking_id.id), ('state', '=', 'draft')])
        for sms in sms_lines:
            sms.write({
                'state': 'cancelled',
            })
