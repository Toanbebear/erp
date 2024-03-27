import json
import logging
from datetime import datetime, timedelta

import requests

from odoo import models
from odoo import tools

_logger = logging.getLogger(__name__)


class CrmSms(models.Model):
    _inherit = 'crm.sms'

    def _send_sms(self):
        res = super(CrmSms, self)._send_sms()
        start_time = datetime.now()
        config = self.env['ir.config_parameter'].sudo()

        """
            Kiểm tra trong cấu hình có tham số cho phép gửi sms thì mới gửi
            Cấu hình trong file config:
                zns_care_soft_enable = True
        """
        has_zns = 'zns_care_soft_enable' in tools.config.options and tools.config['zns_care_soft_enable']
        is_prod = 'production' == config.get_param('environment')
        if is_prod and has_zns:
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
                                                    ('desc', '!=', False), ('type', '=', 'zns')],
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
                        # Xử lý gửi Zalo Notification Service
                        # Lưu content dạng json:
                        # {
                        #         "template_id": 7156,
                        #         "params": {
                        #             "ma_booking": "BOOKING123",
                        #             "customer_name": "Tên khách hàng",
                        #             "booking_date": "22/12/2023"
                        #         }
                        obj_zns = json.loads(content)
                        template_id = obj_zns['template_id']
                        params = obj_zns['params']
                        res = self._zns_cs(domain, token, phone, template_id, params)
                        count_zns += 1

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
        return res

    def _zns_cs(self, domain, token, phone, template_id, params):

        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }

        data = {
            "zns": {
                "phone": phone,
                "template_id": template_id,
                "ticket_id": 0,
                "params": params,
            }
        }

        url = "%s/api/v1/zalo/zns" % domain
        _logger.info("Send headers %s data %s", headers, data)
        res = requests.post(url, headers=headers, data=json.dumps(data))
        _logger.info("Response %s", res)

        if res.status_code == 200:
            return json.loads(res.content.decode())
        else:
            return {'code': 'error'}
