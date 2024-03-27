import logging
import time
import requests

from odoo.http import request

_logger = logging.getLogger(__name__)


def get_url_sale():
    config = request.env['ir.config_parameter'].sudo()
    url_ehc = config.get_param('url_sale')
    return url_ehc


def get_token_sale():
    config = request.env['ir.config_parameter'].sudo()
    username = config.get_param('username_acc_api_sale')
    pwd = config.get_param('password_acc_api_sale')
    url_ehc = get_url_sale()

    url = url_ehc + '/api/auth/token'

    data = {
        "login": username,
        "password": pwd
    }

    response = requests.get(url, data=data)
    response = response.json()
    return response['access_token']


def retry(times=5, interval=3):
    def wrapper(func):
        def wrapper(*arg, **kwarg):
            for i in range(times):
                try:
                    return func(*arg, **kwarg)
                except:
                    time.sleep(interval)
                    continue
            # TODO ghi lại các bản ghi bị lỗi - hiện tại đang cho pass
            pass

        return wrapper

    return wrapper


def get_source_seeding():
    sources = request.env['utm.source'].sudo().search([('check_sync_seeding', '=', True)])
    return sources


def get_source_ctv():
    sources = request.env['utm.source'].sudo().search([('check_sync_ctv', '=', True)])
    return sources
