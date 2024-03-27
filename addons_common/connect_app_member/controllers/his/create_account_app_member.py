# Part of odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime
from odoo.addons.connect_app_member.controllers.app_member_common import app_member_validate_token, response
from odoo.http import request
import json

from odoo import http

_logger = logging.getLogger(__name__)


class CreateAccountAppMember(http.Controller):
    @app_member_validate_token
    @http.route("/api/app-member/v1/create_account", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_create_account(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        partner = request.env['res.partner'].sudo().search(['|',('phone','=',body['phone']),('mobile','=',body['phone'])])
        value = {
            'phone': body['phone'],
            'name': body['name'],
            'partner_id': partner.id if partner else None
        }
        account = request.env['account.app.member'].sudo().search([('phone','=',body['phone'])])
        if not account:
            request.env['account.app.member'].sudo().create(value)