# -*- coding: utf-8 -*-
# Part of odoo. See LICENSE file for full copyright and licensing details.
import datetime
import json
import logging
import werkzeug

from odoo.addons.sci_seeding.controllers.common import seeding_validate_token

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SeedingUserController(http.Controller):
    @seeding_validate_token
    @http.route("/api/v1/create-seeding-user", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_create_seeding_user(self, **payload):
        """ Tạo danh sách seeding user """
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= Cập nhật danh sách seeding user ==================')
        _logger.info('body: %s' % body)
        field_require = [
            'name',
            'phone'
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': False,
                    'message': 'Thiếu tham số %s!!!' % field
                }
        seeding_user = request.env['seeding.user'].sudo().create({
            'code_user': body['code_user'],
            'name': body['name'],
            'phone': body['phone']
        })
        _logger.info(seeding_user)
        _logger.info('============================================================================')
        if seeding_user:
            return {
                'status': 0,
                'message': {
                    'type': 0,
                    'content': 'Thành công'
                },
                'data': seeding_user.id
            }
