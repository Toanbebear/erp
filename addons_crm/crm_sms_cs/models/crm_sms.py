import json
import logging
from datetime import datetime, timedelta

import requests

from odoo import api, tools
from odoo import models, fields

_logger = logging.getLogger(__name__)


class CrmSms(models.Model):
    _inherit = 'crm.sms'

    state = fields.Selection(
        [('draft', 'Chưa gửi'), ('sent', 'Đã gửi'), ('error', 'Gửi lỗi'),
         ('cancelled', 'Cancelled')], default='draft', string="Status")
    cs_response = fields.Char()

    type = fields.Selection([('sms', 'SMS'), ('zns', 'Zalo')], default='sms', string="Kiểu")

    @api.model
    def create(self, values):
        if 'type' not in values:
            values['type'] = 'sms'
        return super(CrmSms, self).create(values)

    @api.onchange('active')
    def _onchange_active(self):
        if self.active == False:
            self.state = 'cancelled'

    def _send_sms(self):
        start_time = datetime.now()
        config = self.env['ir.config_parameter'].sudo()

        # _logger.info(config.get_param('environment'))
        # _logger.info(tools.config['sms_caresoft_enable'])

        """
            Kiểm tra trong cấu hình có tham số cho phép gửi sms thì mới gửi
            Cấu hình trong file config:
                sms_care_soft_enable = True
                zns_care_soft_enable = True
        """
        has_sms = 'sms_care_soft_enable' in tools.config.options and tools.config['sms_care_soft_enable']
        is_prod = 'production' == config.get_param('environment')
        if is_prod and has_sms:
            # Lấy account thương hiệu và token bên caresoft
            cs_account = {}
            brands = self.env['res.brand'].search([])
            for brand in brands:
                cs_account[brand.id] = {
                    'domain': config.get_param('domain_caresoft_%s' % (brand.code.lower())),
                    'token': config.get_param('domain_caresoft_token_%s' % (brand.code.lower())),
                    'service_id': config.get_param('domain_caresoft_service_id_%s' % (brand.code.lower()))
                }

            # Tìm tất cả những sms có ngày gửi trong khoảng trước thời điểm chạy job 10p và sau đó 10p
            start_time = datetime.now() - timedelta(minutes=10)
            end_time = datetime.now() + timedelta(minutes=10)

            sms_lines = self.env['crm.sms'].search([('active', '=', True),
                                                    ('state', '=', 'draft'),
                                                    ('send_date', '>=', start_time),
                                                    ('send_date', '<=', end_time),
                                                    ('phone', '!=', False),
                                                    ('desc', '!=', False), ('type', '=', 'sms')],
                                                   order='send_date asc')
            count = 0
            count_zns = 0
            for sms in sms_lines:
                brand_id = sms.brand_id.id
                if brand_id in cs_account:
                    domain = cs_account[brand_id]['domain']
                    service_id = cs_account[brand_id]['service_id']
                    token = cs_account[brand_id]['token']
                    content = sms.desc
                    phone = sms.phone

                    # Có số điện thoại và nội dung mới thực hiện tiếp
                    if phone and content:
                        res = self._sms_cs(domain, token, service_id, content, phone)
                        count += 1

                        # TODO Cho log cs_response ra bảng log, để dễ dàng clear log đi khi đầy
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
            _logger.info("_________________Number of SMS: %s" % count)
            _logger.info("_________________Number of ZNS: %s" % count_zns)

        _logger.info("RUNJOB: _send_sms TIME: %s" % (datetime.now() - start_time))

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
