# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, get_brand_id_hh

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SourceGroupUserEHCController(http.Controller):
    @ehc_validate_token
    @http.route("/api/v1/update-source-group-user", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_ehc_update_source_group_user(self, **payload):
        """
            3.1 API cập nhật danh sách nhóm người giới thiệu
        """
        # get body
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= 3.1 API cập nhật danh sách nhóm người giới thiệu ==================')
        _logger.info(body)
        _logger.info('=================================================================================')

        field_require = [
            'source_group_user_code',
            'source_group_user_name',
            'stage',
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thieu tham so %s!!!' % field
                }

        source_group_ehc = request.env['crm.category.source'].sudo().search([('code', '=', body['source_group_user_code'])])
        value = {
                'name': body['source_group_user_name'],
                'code': body['source_group_user_code'],
                'stage': str(body['stage']),
                'brand_id': get_brand_id_hh()
            }
        if source_group_ehc:
            result = source_group_ehc.sudo().write(value)
            if result:
                return {
                    'stage': 0,
                    'message': 'Cap nhat nhom nguoi gioi thieu thanh cong!'
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Cap nhat nhom nguoi gioi thieu that bai!!!'
                }
        else:
            result = source_group_ehc.sudo().create(value)
            if result:
                return {
                    'stage': 0,
                    'message': 'Cap nhat nhom nguoi gioi thieu thanh cong!'
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Cap nhat nhom nguoi gioi thieu that bai!!!'
                }

