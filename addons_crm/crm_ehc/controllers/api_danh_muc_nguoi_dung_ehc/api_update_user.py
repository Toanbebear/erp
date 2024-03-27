# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class UserEHCController(http.Controller):
    @ehc_validate_token
    @http.route("/api/v1/update-user", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_ehc_update_user(self, **payload):
        """
            2.2 API cập nhật người dùng EHC-HIS
        """
        # get body
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= 2.2 API cập nhật người dùng EHC-HIS ==================')
        _logger.info(body)
        _logger.info('=================================================================================')

        field_require = [
            'user_id',
            'user_code',
            'user_name',
            'user_phone',
            'user_name_practicing_certificate',
            'user_code_practicing_certificate',
            # 'id_department',
            'user_type_id',
            'stage',
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thieu tham so %s!!!' % field
                }

        user_ehc = request.env['crm.hh.ehc.user'].sudo().search([('user_code', '=', body['user_code'])])
        value = {
            'user_id': body['user_id'],
            'user_name': body['user_name'],
            'user_phone': body['user_phone'],
            'user_name_practicing_certificate': body['user_name_practicing_certificate'],
            'user_code_practicing_certificate': body['user_code_practicing_certificate'],
            # 'id_department': body['id_department'],
            'user_stage': str(body['stage']),
            'user_type_id': body['user_type_id'],
        }
        if user_ehc:
            result = user_ehc.sudo().write(value)
            if result:
                return {
                    'stage': 0,
                    'message': 'Cap nhat nguoi dung thanh cong!'
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Cap nhat nguoi dung that bai!!!'
                }
        else:
            value['user_code'] = body['user_code']
            result = user_ehc.sudo().create(value)
            if result:
                return {
                    'stage': 0,
                    'message': 'Cap nhat nguoi dung thanh cong!'
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Cap nhat nguoi dung that bai!!!'
                }

