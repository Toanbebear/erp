import logging

import requests

from odoo import fields, models
from odoo.addons.crm_ehc.models.ehc_common import get_token_ehc, get_url_ehc, get_api_code_ehc

_logger = logging.getLogger(__name__)


class ServiceDepartmentEHC(models.Model):
    _name = "crm.hh.ehc.user"
    _description = 'User EHC'
    _rec_name = "user_name"

    user_id = fields.Integer('ID EHC')
    user_code = fields.Char('Tên đăng nhập')
    user_name = fields.Char('Tên người dùng')
    user_phone = fields.Char('SĐT')
    user_name_practicing_certificate = fields.Char('Họ tên đăng ký CCHN')
    user_code_practicing_certificate = fields.Char('Mã CCHN')
    # id_department
    user_type_id = fields.Char('Vị trí công việc')
    user_stage = fields.Selection([('0', 'Đang hoạt động'), ('1', 'Không hoạt động')])

    def cron_get_user_ehc(self):
        token = get_token_ehc()
        url = get_url_ehc()
        api_code = get_api_code_ehc()

        url = url + '/api/user?api=%s' % api_code

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token
        }

        r = requests.get(url, headers=headers)
        response = r.json()
        if 'status' in response and int(response['status']) == 0:
            for rec in response['data']:
                user_code = rec['user_code']
                value = {
                    'user_id': rec['user_id'],
                    'user_code': rec['user_code'],
                    'user_name': rec['user_name'],
                    'user_phone': rec['user_phone'],
                    'user_name_practicing_certificate': rec['user_name_practicing_certificate'],
                    'user_code_practicing_certificate': rec['user_code_practicing_certificate'],
                    # 'user_type_id': rec['user_type_id'],
                    'user_stage': str(rec['stage']),
                }
                user_ehc = self.env['crm.hh.ehc.user'].sudo().search([('user_code', '=', user_code)], limit=1)
                if user_ehc:
                    user_ehc.sudo().write(value)
                else:
                    user_ehc.sudo().create(value)