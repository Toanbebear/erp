# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, get_brand_id_hh

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SourceUserEHCController(http.Controller):
    @ehc_validate_token
    @http.route("/api/v1/update-source-user", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_ehc_update_source_user(self, **payload):
        """
            4.1 API cập nhật danh sách người giới thiệu
        """
        # get body
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= 4.1 API cập nhật danh sách người giới thiệu ==================')
        _logger.info(body)
        _logger.info('=================================================================================')

        field_require = [
            'source_user_code',
            'source_user_name',
            'source_group_user_code',
            'stage',
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thieu tham so %s!!!' % field
                }

        source_ehc = request.env['utm.source'].sudo().search([('code', '=', body['source_user_code'])])
        value = {
                'name': body['source_user_name'],
                'code': body['source_user_code'],
                'stage': str(body['stage']),
                'brand_id': get_brand_id_hh()
            }
        if 'source_group_user_code' in body and body['source_group_user_code']:
            source_group_ehc = request.env['crm.category.source'].sudo().search(
                [('code', '=', body['source_group_user_code'])])
            if source_group_ehc:
                value['category_id'] = source_group_ehc.id
            else:
                pass
                # TODO gọi lại cron lấy người giới thiệu trên EHC
        if 'source_user_phone' in body and body['source_user_phone']:
            value['source_user_phone'] = body['source_user_phone']
        if 'source_user_address' in body and body['source_user_address']:
            value['source_user_address'] = body['source_user_address']
        if 'source_user_bank_account' in body and body['source_user_bank_account']:
            value['source_user_bank_account'] = body['source_user_bank_account']

        if source_ehc:
            result = source_ehc.sudo().write(value)
            if result:
                return {
                    'stage': 0,
                    'message': 'Cap nhat nguoi gioi thieu thanh cong!'
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Cap nhat nguoi gioi thieu that bai!!!'
                }
        else:
            result = source_ehc.sudo().create(value)
            if result:
                return {
                    'stage': 0,
                    'message': 'Cap nhat nguoi gioi thieu thanh cong!'
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Cap nhat nguoi gioi thieu that bai!!!'
                }

