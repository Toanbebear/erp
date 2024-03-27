import json
import logging
from datetime import datetime, timedelta
import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    # Đông Á
    # def app_member_da_cron_send_reminders_to_customers(self):
    #     params = self.env['ir.config_parameter'].sudo()
    #     domain = params.get_param('config_domain_app_member_da')
    #     if domain:
    #         headers = {'Content-type': 'application/json'}
    #
    #         # Tìm tất cả những bk đến lịch
    #         start_time = datetime.now().date() - timedelta(days=1)
    #         end_time = datetime.now().date() + timedelta(days=1)
    #         acountes = self.get_account_app_member_da()
    #
    #         datas = self.env['crm.sms'].sudo().search([('phone', 'in', acountes), ('send_date', '>', start_time), ('send_date', '<', end_time), ('brand_id.code', '=', 'DA')])
    #
    #         temp = self.get_temp_notification_reminders()
    #
    #         for data in datas:
    #             if 'Nhắc hẹn khách hàng lần 1' in data.name:
    #                 content = temp['content']
    #
    #                 # content = content.replace('[Service_name]', str(data.crm_id.crm_line_ids.service_id.mapped('name')))
    #                 content = content.replace('[Service_name]', '; '.join(data.crm_id.crm_line_ids.service_id.mapped('name')))
    #                 content = content.replace('[Date]', data.crm_id.booking_date.strftime('%Y-%m-%d'))
    #                 content = content.replace('[Branch_name]', data.company_id.name)
    #
    #                 payload = {
    #                     "phone": data.phone,
    #                     # "phone": "0393923233",
    #                     "content": content,
    #                     "object_id": temp['object_id'],
    #                     "code_company": data.company_id.code,
    #                     "notify_type": 6,
    #                 }
    #                 response = requests.post('%s/api/v1/push-noti' % domain, headers=headers, data=json.dumps(payload))
    #     else:
    #         pass
    #
    # def get_account_app_member_da(self):
    #     params = self.env['ir.config_parameter'].sudo()
    #     domain = params.get_param('config_domain_app_member_da')
    #     headers = {'Content-type': 'application/json'}
    #     payload = json.dumps({})
    #     response = requests.get('%s/api/v1/noti/get-account' % domain, headers=headers, data=payload)
    #     response = response.json()
    #     if 'result' in response and response['result'] and int(response['result']['stage']) == 0:
    #         return response['result']['data']
    #
    # def get_temp_notification_reminders(self):
    #     params = self.env['ir.config_parameter'].sudo()
    #     domain = params.get_param('config_domain_app_member_da')
    #     headers = {'Content-type': 'application/json'}
    #     payload = json.dumps({})
    #     response = requests.get('%s/api/v1/noti/get-temp-appointment-reminder' % domain, headers=headers, data=payload)
    #     response = response.json()
    #     if 'result' in response and response['result'] and int(response['result']['stage']) == 0:
    #         return response['result']['data']

