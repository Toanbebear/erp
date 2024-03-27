import json

import requests

from odoo.http import request


def get_url():
    ir_config = request.env['ir.config_parameter'].sudo()
    url = ir_config.get_param('url_ctv_hh')
    return url


def get_login():
    ir_config = request.env['ir.config_parameter'].sudo()
    login = ir_config.get_param('login_ctv_hh')
    return login


def get_pwd():
    ir_config = request.env['ir.config_parameter'].sudo()
    pwd = ir_config.get_param('pwd_ctv_hh')
    return pwd


def get_token():
    url = get_url()
    url = url + "/api/auth/token"
    payload = json.dumps({
        "login": get_login(),
        "password": get_pwd()
    })
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    rs = response.json()['result']
    if rs['status'] == 0:
        return rs['data']['access_token']
    return False
