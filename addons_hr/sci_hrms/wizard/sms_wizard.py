# -*- coding: utf-8 -*-
#############################################################################
from odoo import models, api, fields
import requests
from odoo.exceptions import ValidationError

class WhatsappSendMessage(models.TransientModel):

    _name = 'sms.message'
    _description = 'SMS message'

    user_id = fields.Many2one('hr.employee', string="Nhân viên")
    mobile = fields.Char(related='user_id.mobile_phone', required=True)
    message = fields.Text(string="message", required=True)
    url = fields.Text(string="Url")
    params = fields.Text(string="Params")
    result = fields.Text(string="Result")

    def send_message(self):
        if self.message and self.mobile:
            ESMS = self.env['ir.config_parameter'].sudo()
            esms_url = ESMS.get_param('esms.esms_url', default='')
            esms_brand_name = ESMS.get_param('esms.esms_brand_name', default='')
            esms_api_key = ESMS.get_param('esms.esms_api_key', default='')
            esms_secret_key = ESMS.get_param('esms.esms_secret_key', default='')
            get_res = {'Phone': self.mobile,
                       'Content': self.message,
                       'ApiKey': esms_api_key,
                       'SecretKey': esms_secret_key,
                       'Brandname': esms_brand_name,
                       'SmsType': 2}
            try:
                response = requests.get(esms_url, params=get_res)
            except Exception:
                raise ValidationError(_('Invalid Data!.'))
            res_con = response.json()
            self.url = esms_url
            self.params = get_res
            self.result = response.json()
            if res_con.get('CodeResult') == 100:
                return True
            else:
                return False
