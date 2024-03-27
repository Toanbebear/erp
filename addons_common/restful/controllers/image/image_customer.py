from odoo.addons.restful.common import (
    extract_arguments
)
from odoo.addons.restful.controllers.main import (
    validate_token,
)

import json
import logging
from odoo import http
from odoo.http import request
from odoo.tools.image import image_data_uri

_logger = logging.getLogger(__name__)


class ImageCustomerController(http.Controller):

    @validate_token
    @http.route("/api/v1/image-customer", type="http", auth="none", methods=["GET"], csrf=False)
    def get_image_customer(self, **payload):
        """ API 1.16 Lấy ảnh khách hàng"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        phone = payload.get("phone", None)
        if phone:
            domain = ['|', '|', ('phone', '=', phone), ('mobile', '=', phone), ('phone_no_3', '=', phone)]
        code = payload.get("code", None).upper()
        if code:
            domain.append(('code_customer', '=', code))
        partner = request.env['res.partner'].sudo().search(domain)
        if partner:
            street = partner.street + ', ' if partner.street else ''
            district = partner.district_id.name + ', ' if partner.district_id else ''
            state = partner.state_id.name + ', ' if partner.state_id else ''
            country = partner.country_id.name if partner.country_id else ''
            data = {'avatar': image_data_uri(partner.image_1920) if partner.image_1920 else '',
                    'id': partner.id,
                    'name': partner.name,
                    'code': partner.code_customer,
                    'address': street + district + state + country,
                    'birthday': partner.birth_date.strftime("%d-%m-%Y") if partner.birth_date else '',
                    'age': partner.age if partner.age else '-'}
            return json.dumps({
                'status': 0,
                'massage': "Success",
                'data': data
            })
        else:
            return json.dumps({
                'status': 1,
                'message': 'Không tìm thấy thông tin'
            })
