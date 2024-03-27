import json

import requests

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError

class InheritResCompany(models.Model):
    _inherit = 'res.company'

    url_his_83 = fields.Char('Domain 83 tiêu chí')
    user_his = fields.Char('Tài khoản')
    pass_his = fields.Char('Mật khẩu')
    token_his = fields.Char('Token')

    def get_token_his(self):
        if self.user_his and self.pass_his and self.url_his_83:
            url = self.url_his_83 + "/api/erp/token"
            login = self.user_his
            password = self.pass_his
            payload = json.dumps({
                "login": login,
                "password": password
            })
            headers = {
                'login': login,
                'password': password,
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            response = response.json()
            if response['access_token']:
                self.token_his = response['access_token']
            else:
                raise ValidationError(_('Không tìm thấy dữ liệu. Yêu cầu điền lại đúng thông tin'))
        else:
            raise ValidationError(_('Chưa điền đủ thông tin'))


