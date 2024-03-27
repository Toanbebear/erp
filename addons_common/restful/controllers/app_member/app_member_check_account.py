# Part of odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo.addons.restful.controllers.app_member.app_member_common import app_member_validate_token, response
from odoo.http import request
import json

from odoo import http

_logger = logging.getLogger(__name__)


class CheckAccountAppMemberController(http.Controller):
    @app_member_validate_token
    @http.route("/api/v1/check-account-app-member", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_check_account_app_member(self, **payload):
        """
            API check partner ERP
        """
        # TODO tạo api cho phép check 1 mảng các số điện thoại, trả về danh sách các số đó và kết quả có hay ko từng số
        body = json.loads(request.httprequest.data.decode('utf-8'))
        if 'phone' in body and body['phone']:
            partner = request.env['res.partner'].sudo().search(['|', ('phone', '=', body['phone']),
                                                                ('mobile', '=', body['phone'])], limit=1)
            if partner:
                data = {
                    'phone': body['phone'],
                    'name': partner.name if partner.name else None,
                    'birth_date': partner.birth_date if partner.birth_date else None,
                    'gender': partner.gender if partner.gender else None,
                }
                return {
                    'data': data,
                    'stage': True,
                    'message': 'Đã có partner trên ERP'
                }
            else:
                return {
                    'stage': False,
                    'message': 'Chưa có partner trên ERP'
                }

    @app_member_validate_token
    @http.route("/api/v1/check-account-app-member-1", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_check_account_app_member_1(self, **payload):
        """
            API check partner ERP
        """
        # TODO tạo api cho phép check 1 mảng các số điện thoại, trả về danh sách các số đó và kết quả có hay ko từng số
        body = json.loads(request.httprequest.data.decode('utf-8'))
        if 'list_phone' in body and body['list_phone']:
            list_data = []
            for phone in body['list_phone']:
                partner = request.env['res.partner'].sudo().search(['|', ('phone', '=', phone),
                                                                    ('mobile', '=', phone)], limit=1)
                if partner:
                    data = {
                        'phone': phone,
                        'name': partner.name if partner.name else None,
                        'birth_date': partner.birth_date if partner.birth_date else None,
                        'gender': partner.gender if partner.gender else None,
                    }
                    list_data.append(data)
            if list_data:
                return {
                    'data': list_data,
                    'stage': True,
                    'message': 'Đã có partner trên ERP'
                }
            else:
                return {
                    'stage': False,
                    'message': 'Chưa có partner trên ERP'
                }
