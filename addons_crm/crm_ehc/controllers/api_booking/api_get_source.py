
# Part of odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, response

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class GetSourceController(http.Controller):
    @ehc_validate_token
    @http.route("/api/v1/get-source", type="http", auth="none", methods=["GET"], csrf=False)
    def get_source(self, **payload):
        """ Danh sách nguồn CRM"""
        data = []
        sources = request.env['utm.source'].sudo().search([('active', '=', True)])
        for rec in sources:
            data.append({
                'id': rec.id,
                'name': rec.name,
                'code': rec.code,
                'category_name': rec.category_id.name
            })
        if data:
            return response(data=data,status=0,message_content='Lấy dữ liêu nguồn thành công!!!')
        else:
            return response(data=data, status=1, message_content='Lấy dữ liêu nguồn thất bại!!!')
