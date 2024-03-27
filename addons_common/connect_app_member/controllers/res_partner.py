import logging
from datetime import datetime
from odoo.addons.connect_app_member.controllers.app_member_common import app_member_validate_token, response
from odoo.http import request
import json

from odoo import http

_logger = logging.getLogger(__name__)


class GetAccountPartner(http.Controller):

    @app_member_validate_token
    @http.route("/api/app-member/v1/get-max-id", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_max_id(self, **payload):
        request.env.cr.execute(""" 
                                           select MAX(id) from res_partner""")
        max_id = request._cr.fetchall()
        if max_id:
            return {
                'stage': 0,
                'message': 'Thành công',
                'max_id': max_id[0]
            }

    @app_member_validate_token
    @http.route("/api/app-member/v1/get-account-partner", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_account_partner(self, **payload):
        data = []
        body = json.loads(request.httprequest.data.decode('utf-8'))
        list_partner = request.env['res.partner'].sudo().search(
            [('id', '>', body['id_max']), ('id', '<=', body['last_id_partner'])], order='id', limit=500)
        for partner in list_partner:
            value = {
                'id': partner.id,
                'name': partner.name if partner.name else '',
                'phone': partner.phone if partner.phone else '',
                'mobile': partner.mobile if partner.mobile else '',
                'birth_date': partner.birth_date if partner.birth_date else None
            }
            data.append(value)
        print(len(data))
        if data:
            return {
                'stage': 0,
                'message': 'Thành công',
                'data': data
            }
        else:
            return {
                'stage': 1,
                'message': 'Thất bại',
                'data': {}
            }
