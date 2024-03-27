import json

from odoo import api, models
from ..helper import call_api, create_log

api_url = "onnet_sci_api.accounting_api_url"
database = "onnet_sci_api.database_enterprise"
username = "onnet_sci_api.username_enterprise"
password = "onnet_sci_api.password_enterprise"
access_token = "onnet_sci_api.token_enterprise"

class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    @api.model
    def update_enterprice_token(self):
        path = "/api/auth/token/"

        payload = json.dumps({
            "db": self.env.ref(database).sudo().value,
            "login": self.env.ref(username).sudo().value,
            "password": self.env.ref(password).sudo().value
        })
        headers = {
            'Content-Type': 'application/json'
        }
        url = self.env.ref(api_url).sudo().value + path
        response = call_api('POST', url, payload, headers)
        new_token = ''
        if response.get('result', False):
            if response.get('result').get('data', False):
                new_token = response.get('result').get('data').get('access_token', False)
        if new_token:
            self.env.ref(access_token).sudo().write({'value':new_token})
        create_log(url, 'POST', headers, payload, response, False)
        return True