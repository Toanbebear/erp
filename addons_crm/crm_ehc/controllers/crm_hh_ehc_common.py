"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import datetime
import functools
import json
import logging

import werkzeug.wrappers

from odoo.addons.restful.common import (
    invalid_response,
)
from odoo.http import request

_logger = logging.getLogger(__name__)


def ehc_validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        authorization = request.httprequest.headers.get("Authorization")
        if not authorization:
            return invalid_response(
                "authorization", "missfing authorization in request header", 401
            )
        config = request.env['ir.config_parameter'].sudo()
        result = config.get_param('token_api_connect_ehc')
        if result != authorization:
            return invalid_response(
                "authorization", "authorization seems to have expired or invalid", 401
            )
        return func(self, *args, **kwargs)

    return wrap


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if isinstance(o, bytes):
        return str(o)


# def response(data, message_type, message_content, status, res_status=200):
def response(data, message_content, status, res_status=200):
    """Default Response
    This will be return when the http request was successfully processed."""
    return werkzeug.wrappers.Response(
        status=res_status,
        content_type="application/json; charset=utf-8",
        response=json.dumps({
            "status": status,
            # "message": {
            #     "type": message_type,
            #     "content": message_content
            # },
            "message": message_content,
            "data": data
        },
            default=default),
    )


def get_brand_id_hh():
    brand_id_hh = request.env['res.brand'].sudo().search([('code', '=', 'HH')], limit=1).id
    return brand_id_hh


def get_company_id_hh():
    company_id_hh = request.env['res.company'].sudo().search([('code', '=', 'BVHH.HN.01')], limit=1).id
    return company_id_hh


def get_price_list_id_hh():
    price_list_id_hh = request.env['product.pricelist'].sudo().search([('brand_id.code', '=', 'HH')], limit=1).id
    return price_list_id_hh


def get_user_hh():
    config = request.env['ir.config_parameter'].sudo()
    user = config.get_param('user_name_to_get_context_connect_ehc')
    user_hh = request.env['res.users'].sudo().search([('login', '=', user)]).id
    if user_hh:
        user_hh_id = user_hh
    else:
        user_hh_id = 1
    return user_hh_id


def convert_string_to_date(string):
    # return datetime.datetime(int(string[0:4]), int(string[4:6]), int(string[6:8]), int(string[8:10]),
    #                          int(string[10:12]), int(string[12:14]))
    return datetime.datetime(int(string[0:4]), int(string[4:6]), int(string[6:8]), int(string[8:10]),
                         int(string[10:12]))


def get_address_2(address):
    address = address.replace('Quận', '').replace('Thành phố', '').replace('Huyện', '').replace('TP', '').replace(
        'Thị xã', '').replace('Phường', '').replace('Thị trấn', '').replace('Xã', '')
    return address


# def num2words_vnm(num):
#     under_20 = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'mười một',
#                 'mười hai', 'mười ba', 'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín']
#     tens = ['hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']
#     above_100 = {100: 'trăm', 1000: 'nghìn', 1000000: 'triệu', 1000000000: 'tỉ'}
#
#     if num < 20:
#         return under_20[num]
#
#     elif num < 100:
#         under_20[1], under_20[5] = 'mốt', 'lăm'  # thay cho một, năm
#         result = tens[num // 10 - 2]
#         if num % 10 > 0:  # nếu num chia 10 có số dư > 0 mới thêm ' ' và số đơn vị
#             result += ' ' + under_20[num % 10]
#         return result
#
#     else:
#         unit = max([key for key in above_100.keys() if key <= num])
#         result = num2words_vnm(num // unit) + ' ' + above_100[unit]
#         if num % unit != 0:
#             if num > 1000 and num % unit < unit / 10:
#                 result += ' không trăm'
#             if 1 < num % unit < 10:
#                 result += ' linh'
#             result += ' ' + num2words_vnm(num % unit)
#     return result.capitalize()


def create_log(model_name, input, id_record, response, type_log, name_log, status_code, url, header):
    model = request.env['ir.model'].sudo().search([('model', '=', model_name)])
    if model:
        request.env['api.log'].sudo().create({
            "name": name_log,
            "type_log": type_log,
            "model_id": model.id,
            "id_record": id_record,
            "input": input,
            "response": response,
            "url": url,
            "status_code": status_code,
            "header": header,
        })
